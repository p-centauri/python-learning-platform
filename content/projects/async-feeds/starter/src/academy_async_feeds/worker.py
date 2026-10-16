from collections.abc import Sequence

from .models import BatchReport, Opener, Source


async def ingest(
    sources: Sequence[Source],
    *,
    opener: Opener,
    workers: int = 2,
    queue_size: int = 2,
    timeout: float = 1.0,
) -> BatchReport:
    """Bound tasks/queued work; publish only after complete success/cleanup."""
    raise NotImplementedError("Implement the bounded TaskGroup worker")
