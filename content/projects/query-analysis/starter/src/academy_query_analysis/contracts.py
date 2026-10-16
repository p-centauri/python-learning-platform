from dataclasses import dataclass
import json
from academy_ingestion_service.contracts import field


def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate filter key")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class Filter:
    encoded: str

    def __post_init__(self) -> None:
        if type(self.encoded) is not str or not 1 <= len(self.encoded) <= 512:
            raise ValueError("bounded JSON filter required")
        value: object = json.loads(self.encoded, object_pairs_hook=unique)
        if type(value) is not dict or not 1 <= len(value) <= 2 or not set(value) <= {"kind", "region"}:
            raise ValueError("filter must contain kind/region only")
        for item in value.values():
            if item is not None and (type(item) is not str or len(item) > 32 or not all(c.isprintable() for c in item)):
                raise ValueError("filter values must be null or bounded printable strings")
        object.__setattr__(self, "encoded", json.dumps(value, sort_keys=True, separators=(",", ":")))


@dataclass(frozen=True, slots=True)
class Summary:
    namespace: str
    records: int
    total: int
    noted_records: int


@dataclass(frozen=True, slots=True)
class Revision:
    revision: int
    value: int
    previous: int | None
    delta: int | None
    running_total: int
    latest: bool


@dataclass(frozen=True, slots=True)
class Match:
    id: str
    revision: int
    value: int


def limit(value: int, maximum: int = 32) -> None:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError("invalid result limit")


def scoped(namespace: str) -> None:
    field(namespace)


def copied(filter: Filter) -> Filter:
    if type(filter) is not Filter:
        raise ValueError("exact Filter required")
    return Filter(filter.encoded)
