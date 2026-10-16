from dataclasses import asdict, replace
import json
import re
from typing import TYPE_CHECKING, cast
from academy_retrieval import Chunk, Document, Spec, make_chunks
from academy_retrieval.contracts import identifier, integer, text, vector
from .contracts import Evidence, Record


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def nonfinite(value: str) -> object:
    raise ValueError("non-finite JSON constant")


def parse(raw: object, bound: int) -> object:
    if type(raw) is not bytes or not 1 <= len(raw) <= bound:
        raise ValueError("invalid bounded JSON bytes")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)


def fields(value: object, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError("invalid exact JSON fields")
    return cast(dict[str, object], value)


def array(value: object, cap: int) -> list[object]:
    if type(value) is not list or len(value) > cap:
        raise ValueError("invalid bounded JSON array")
    return cast(list[object], value)


def copied(record: Record, spec: Spec) -> Record:
    if type(record) is not Record or type(spec) is not Spec:
        raise ValueError("exact index inputs required")
    item = replace(record)
    if item.document is None:
        return item
    doc = replace(item.document)
    spans = make_chunks(doc)
    if len(spans) != len(item.vectors):
        raise ValueError("vector/window count mismatch")
    return replace(item, document=doc, vectors=tuple(vector(v, spec.dimensions) for v in item.vectors))


def chunks(records: tuple[Record, ...], spec: Spec) -> tuple[Chunk, ...]:
    result: list[Chunk] = []
    for record in records:
        item = copied(record, spec)
        if item.document is not None:
            doc = item.document
            for span, values in zip(make_chunks(doc), item.vectors, strict=True):
                result.append(Chunk(span, spec, values, doc.topic, doc.groups, doc.active))
    if len(result) > 64:
        raise ValueError("index chunk cap exceeded")
    return tuple(result)


def encode_record(record: Record) -> bytes:
    return canonical(asdict(record))


def decode_record(raw: bytes, spec: Spec) -> Record:
    row = fields(parse(raw, 65536), {"tenant", "id", "revision", "document", "vectors"})
    doc = None
    if row["document"] is not None:
        value = fields(row["document"], {"tenant", "id", "revision", "text", "topic", "groups", "active"})
        if type(value["active"]) is not bool:
            raise ValueError("exact document boolean required")
        doc = Document(
            identifier(value["tenant"]),
            identifier(value["id"]),
            integer(value["revision"], 1, 1000000),
            text(value["text"], 8192),
            identifier(value["topic"]),
            tuple(identifier(g) for g in array(value["groups"], 8)),
            value["active"],
        )
    values = tuple(vector(tuple(array(v, 32)), spec.dimensions) for v in array(row["vectors"], 32))
    return copied(
        Record(
            identifier(row["tenant"]),
            identifier(row["id"]),
            integer(row["revision"], 1, 1000000),
            doc,
            values,
        ),
        spec,
    )


def evidence_bytes(rows: tuple[Evidence, ...]) -> bytes:
    return canonical(
        [
            {
                "id": row.id,
                "source": asdict(row.span.key),
                "start": row.span.start,
                "end": row.span.end,
                "digest": row.span.digest,
                "text": row.span.text,
            }
            for row in rows
        ]
    )


def terms(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not 1 <= len(value) <= 3:
        raise ValueError("application evidence terms required")
    for term in value:
        if type(term) is not str or re.fullmatch(r"[a-z0-9]{2,32}", term) is None:
            raise ValueError("invalid evidence term")
    if len(set(value)) != len(value):
        raise ValueError("duplicate evidence term")
    return value


def resolve(index: "Index", citation: "Citation", principal: "Principal") -> str | None:
    """Resolve only a still-current authorized exact span, without fetching any URL."""
    from .contracts import Citation
    from academy_retrieval import Principal

    if type(citation) is not Citation or type(principal) is not Principal:
        raise ValueError("exact citation/principal required")
    principal = replace(principal)
    span = replace(citation.span, key=replace(citation.span.key))
    _, records = index.snapshot()
    for item in records:
        doc = item.document
        if doc is None or not doc.active or doc.tenant != principal.tenant:
            continue
        if doc.groups and not set(doc.groups) & set(principal.groups):
            continue
        for current in make_chunks(doc):
            if current == span:
                return current.text
    return None


if TYPE_CHECKING:
    from academy_retrieval import Principal
    from .contracts import Citation
    from .store import Index
