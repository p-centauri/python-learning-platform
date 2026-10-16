from dataclasses import asdict
from hashlib import sha256
import json
from academy_ingest import Record
from academy_feed_objects import FeedKey, Reading, Snapshot
from academy_typed_transforms import Row, map_rows
from .contracts import Item


def fingerprint(item: Item) -> str:
    """Stated synthetic CPU component over frozen service values; not a security hash protocol."""
    raw = json.dumps(
        {"namespace": item.namespace, **asdict(item.datum)}, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    digest = raw
    for _ in range(128):
        digest = sha256(digest + raw).digest()
    return digest.hex()


def snapshot(items: tuple[Item, ...]) -> Snapshot:
    # Deliberately use earlier public value/typed-map interfaces; never widen their limits.
    records = tuple(Record(item.datum.id, item.datum.value) for item in items)
    rows = map_rows(records, lambda record: Row(record.id, record.value))
    return Snapshot(
        Reading(FeedKey(item.namespace, row.id), row.value) for item, row in zip(items, rows, strict=True)
    )


def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON field")
        result[name] = value
    return result
