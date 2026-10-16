"""Implement the three TODOs using README.md; do not weaken the tests."""

from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

MAX_LINE_BYTES = 1024
KINDS = ("api", "db", "worker")


class RecordError(ValueError):
    pass


@dataclass(frozen=True)
class Reading:
    kind: str
    duration_ms: int


def iter_readings(lines: Iterable[bytes]) -> Generator[Reading, None, None]:
    # The unreachable yield keeps this a generator until you implement the body.
    raise NotImplementedError("Parse each line lazily with useful errors")
    yield Reading("api", 0)


@contextmanager
def open_readings(path: Path) -> Iterator[Iterator[Reading]]:
    raise NotImplementedError("Own and close the file and parser")
    yield iter(())


def summarize(readings: Iterable[Reading]) -> dict[str, dict[str, int]]:
    raise NotImplementedError("Consume once and keep fixed group totals")
