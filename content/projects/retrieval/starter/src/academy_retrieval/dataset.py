"""Original packaged development judgments; vectors are supplied by hand, not a model."""

from importlib.resources import files
import json
from typing import cast
from .contracts import (
    Case,
    Chunk,
    Dataset,
    Document,
    Filters,
    Key,
    Principal,
    Query,
    Spec,
    identifier,
    integer,
    text,
    vector,
)
from .operations import make_chunks


def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate fixture key")
        result[key] = value
    return result


def invalid_constant(value: str) -> object:
    raise ValueError("non-finite fixture constant")


def record(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != fields:
        raise ValueError("invalid fixture fields")
    return cast(dict[str, object], value)


def sequence(value: object, bound: int) -> list[object]:
    if type(value) is not list or len(value) > bound:
        raise ValueError("invalid fixture list")
    return cast(list[object], value)


def names(value: object) -> tuple[str, ...]:
    return tuple(identifier(item) for item in sequence(value, 8))


def optional_name(value: object) -> str | None:
    return None if value is None else identifier(value)


def decode_fixture(raw: bytes) -> Dataset:
    if type(raw) is not bytes or not 1 <= len(raw) <= 65536:
        raise ValueError("invalid fixture bytes")
    parsed: object = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)
    data = record(parsed, {"version", "spec", "chunking", "documents", "queries"})
    version = identifier(data["version"])
    config = record(data["spec"], {"model", "version", "dimensions"})
    spec = Spec(
        identifier(config["model"]), identifier(config["version"]), integer(config["dimensions"], 1, 32)
    )
    window = record(data["chunking"], {"width", "overlap"})
    width = integer(window["width"], 16, 512)
    overlap = integer(window["overlap"], 0, width - 1)
    chunks: list[Chunk] = []
    for value in sequence(data["documents"], 16):
        row = record(value, {"tenant", "id", "revision", "text", "topic", "groups", "active", "vectors"})
        if type(row["active"]) is not bool:
            raise ValueError("exact fixture boolean required")
        doc = Document(
            identifier(row["tenant"]),
            identifier(row["id"]),
            integer(row["revision"], 1, 1000000),
            text(row["text"], 8192),
            identifier(row["topic"]),
            names(row["groups"]),
            row["active"],
        )
        spans = make_chunks(doc, width=width, overlap=overlap)
        vectors = sequence(row["vectors"], 32)
        if len(spans) != len(vectors):
            raise ValueError("fixture vector/window count mismatch")
        for span, values in zip(spans, vectors, strict=True):
            chunks.append(
                Chunk(
                    span,
                    spec,
                    vector(tuple(sequence(values, 32)), spec.dimensions),
                    doc.topic,
                    doc.groups,
                    doc.active,
                )
            )
    if len(chunks) > 64:
        raise ValueError("fixture corpus too large")
    cases: list[Case] = []
    for value in sequence(data["queries"], 16):
        row = record(
            value, {"id", "text", "vector", "tenant", "groups", "topic", "document", "min_score", "relevant"}
        )
        threshold = row["min_score"]
        if threshold is not None and type(threshold) not in (int, float):
            raise ValueError("invalid fixture threshold")
        keys: list[Key] = []
        for item in sequence(row["relevant"], 16):
            key = record(item, {"tenant", "document", "revision", "ordinal"})
            keys.append(
                Key(
                    identifier(key["tenant"]),
                    identifier(key["document"]),
                    integer(key["revision"], 1, 1000000),
                    integer(key["ordinal"], 0, 31),
                )
            )
        cases.append(
            Case(
                identifier(row["id"]),
                Query(
                    spec, text(row["text"], 512), vector(tuple(sequence(row["vector"], 32)), spec.dimensions)
                ),
                Principal(identifier(row["tenant"]), names(row["groups"])),
                Filters(
                    optional_name(row["topic"]), optional_name(row["document"]), cast(float | None, threshold)
                ),
                tuple(keys),
            )
        )
    return Dataset(version, spec, tuple(chunks), tuple(cases))


def load_fixture() -> Dataset:
    with files("academy_retrieval").joinpath("fixture.json").open("rb") as stream:
        return decode_fixture(stream.read(65537))
