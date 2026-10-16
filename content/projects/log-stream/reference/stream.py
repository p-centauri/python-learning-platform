"""Maintainer reference, excluded from learner downloads."""

from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
from typing import BinaryIO

MAX_LINE_BYTES = 1024
KINDS = ("api", "db", "worker")


class RecordError(ValueError):
    pass


@dataclass(frozen=True)
class Reading:
    kind: str
    duration_ms: int


def iter_readings(lines: Iterable[bytes]) -> Generator[Reading, None, None]:
    for number, raw in enumerate(lines, 1):
        if len(raw) > MAX_LINE_BYTES:
            raise RecordError(f"line {number}: record exceeds byte limit")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RecordError(f"line {number}: invalid UTF-8") from exc
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RecordError(f"line {number}: invalid JSON") from exc
        if not isinstance(value, dict) or set(value) != {"kind", "duration_ms"}:
            raise RecordError(f"line {number}: expected kind and duration_ms")
        kind = value["kind"]
        duration = value["duration_ms"]
        if not isinstance(kind, str) or kind not in KINDS:
            raise RecordError(f"line {number}: unknown kind")
        if isinstance(duration, bool) or not isinstance(duration, int) or not 0 <= duration <= 60000:
            raise RecordError(f"line {number}: duration_ms must be an integer from 0 to 60000")
        yield Reading(kind, duration)


def bounded_lines(source: BinaryIO) -> Iterator[bytes]:
    while True:
        line = source.readline(MAX_LINE_BYTES + 1)
        if not line:
            return
        yield line


@contextmanager
def open_readings(path: Path) -> Iterator[Iterator[Reading]]:
    with path.open("rb") as source:
        records = iter_readings(bounded_lines(source))
        try:
            yield records
        finally:
            records.close()


def summarize(readings: Iterable[Reading]) -> dict[str, dict[str, int]]:
    totals = {kind: {"count": 0, "total_ms": 0} for kind in KINDS}
    for reading in readings:
        totals[reading.kind]["count"] += 1
        totals[reading.kind]["total_ms"] += reading.duration_ms
    return totals
