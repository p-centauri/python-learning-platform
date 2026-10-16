from collections.abc import Iterable
from academy_ingestion_service import Cursor, Datum, Page
from academy_ingestion_service.contracts import ConflictingDatum
from academy_feed_objects import FeedKey
from academy_measured_cache import CacheKey, LruCache
from .contracts import Analysis, Item
from .support import fingerprint, snapshot


def decode_page(payload: object) -> Page:
    if type(payload) is not dict or set(payload) != {"items", "next_cursor"}:
        raise ValueError("invalid page envelope")
    rows = payload["items"]
    if type(rows) is not list or len(rows) > 32:
        raise ValueError("invalid page items")
    saved: list[Datum] = []
    for row in rows:
        if type(row) is not dict or set(row) != {"id", "revision", "value"}:
            raise ValueError("invalid public row")
        datum = Datum(row["id"], row["revision"], row["value"])
        if saved and (datum.id, datum.revision) <= (saved[-1].id, saved[-1].revision):
            raise ValueError("page keys must strictly increase")
        saved.append(datum)
    raw = payload["next_cursor"]
    cursor = None
    if raw is not None:
        if type(raw) is not dict or set(raw) != {"id", "revision"}:
            raise ValueError("invalid page cursor")
        cursor = Cursor(raw["id"], raw["revision"])
        if not saved or (cursor.id, cursor.revision) != (saved[-1].id, saved[-1].revision):
            raise ValueError("cursor must name last returned row")
    return Page(tuple(saved), cursor)


def prepare(namespace: str, rows: Iterable[Datum]) -> tuple[Item, ...]:
    FeedKey(namespace, "scope")
    seen: dict[tuple[str, int], int] = {}
    latest: dict[str, Item] = {}
    for index, row in enumerate(rows):
        if index == 256:
            raise ValueError("too many source rows")
        if type(row) is not Datum:
            raise ValueError("exact Datum required")
        datum = Datum(row.id, row.revision, row.value)
        key = (datum.id, datum.revision)
        if key in seen and seen[key] != datum.value:
            raise ConflictingDatum()
        seen[key] = datum.value
        # Validate even obsolete values against the previous library's narrower 0..60000 domain.
        item = Item(namespace, datum)
        previous = latest.get(datum.id)
        if previous is None or datum.revision > previous.datum.revision:
            latest[datum.id] = item
        if len(latest) > 64:
            raise ValueError("too many distinct readings")
    return tuple(latest[id] for id in sorted(latest))


def analyse(items: tuple[Item, ...], requests: tuple[int, ...], *, cached: bool = False) -> Analysis:
    if type(items) is not tuple or len(items) > 64 or type(requests) is not tuple or len(requests) > 256:
        raise ValueError("invalid reporting batch")
    if type(cached) is not bool:
        raise ValueError("exact bool mode required")
    copied: list[Item] = []
    for item in items:
        if type(item) is not Item:
            raise ValueError("exact Item required")
        copied.append(Item(item.namespace, Datum(item.datum.id, item.datum.revision, item.datum.value)))
    # Snapshot checks distinct keys, retaining the previous ordering and value bounds.
    snap = snapshot(tuple(copied))
    for position in requests:
        if type(position) is not int or not 0 <= position < len(copied):
            raise ValueError("invalid requested position")
    cache = LruCache[str](8)
    values: list[str] = []
    for position in requests:
        item = copied[position]
        if cached:
            key = CacheKey(item.namespace, item.datum.id, item.datum.revision)
            values.append(cache.get_or_compute(key, lambda: fingerprint(item)))
        else:
            values.append(fingerprint(item))
    info = cache.info()
    return Analysis(snap, tuple(values), info.misses if cached else len(requests), info.hits, info.size)
