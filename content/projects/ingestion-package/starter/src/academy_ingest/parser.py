from collections.abc import Generator, Iterable

from .models import Record


def iter_records(chunks: Iterable[bytes]) -> Generator[Record, None, None]:
    """Borrow chunk input; decode bounded NDJSON lines lazily. See README."""
    raise NotImplementedError("Implement the streamed parser")
    yield  # Keeps the starter a generator; no source reads at construction.


def summarize(records: Iterable[Record]) -> dict[str, int]:
    """One pass, fresh counters, no retained list of records."""
    raise NotImplementedError("Implement count and total")
