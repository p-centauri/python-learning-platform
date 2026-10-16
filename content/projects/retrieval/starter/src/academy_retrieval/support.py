from dataclasses import replace
import math
import re
from .contracts import Chunk, Filters, Principal, Query, vector


def cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    ln = math.hypot(*left)
    rn = math.hypot(*right)
    value = math.fsum((a / ln) * (b / rn) for a, b in zip(left, right, strict=True))
    return max(-1.0, min(1.0, value))


def lexical(left: str, right: str) -> float:
    a = set(re.findall(r"[a-z0-9]+", left.lower()))
    b = set(re.findall(r"[a-z0-9]+", right.lower()))
    return len(a & b) / len(a | b) if a | b else 0.0


def eligible(
    chunks: tuple[Chunk, ...], query: Query, principal: Principal, filters: Filters
) -> tuple[Chunk, ...]:
    """Revalidate copied finite corpus and select latest before filtering; scoring must happen later."""
    if (
        type(chunks) is not tuple
        or len(chunks) > 64
        or type(query) is not Query
        or type(principal) is not Principal
        or type(filters) is not Filters
    ):
        raise ValueError("invalid bounded retrieval input")
    replace(query, spec=replace(query.spec), values=vector(query.values, query.spec.dimensions))
    replace(principal)
    replace(filters)
    saved: list[Chunk] = []
    seen = set()
    latest: dict[tuple[str, str], int] = {}
    for row in chunks:
        if type(row) is not Chunk:
            raise ValueError("exact corpus chunk required")
        copied = replace(
            row,
            span=replace(row.span, key=replace(row.span.key)),
            spec=replace(row.spec),
            values=vector(row.values, row.spec.dimensions),
        )
        if copied.spec != query.spec:
            raise ValueError("model/version/dimension mismatch")
        key = copied.span.key
        if key in seen:
            raise ValueError("duplicate complete chunk key")
        seen.add(key)
        latest[(key.tenant, key.document)] = max(latest.get((key.tenant, key.document), 0), key.revision)
        saved.append(copied)
    return tuple(
        row
        for row in saved
        if row.span.key.revision == latest[(row.span.key.tenant, row.span.key.document)]
        and row.span.key.tenant == principal.tenant
        and row.active
        and (not row.groups or bool(set(row.groups) & set(principal.groups)))
        and (filters.topic is None or row.topic == filters.topic)
        and (filters.document is None or row.span.key.document == filters.document)
    )
