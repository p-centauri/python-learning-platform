from collections.abc import AsyncGenerator, AsyncIterable

from .models import Record


async def iter_records(chunks: AsyncIterable[bytes]) -> AsyncGenerator[Record, None]:
    """Borrow chunks, frame strict bounded NDJSON lazily; see README."""
    raise NotImplementedError("Implement the async framed parser")
    yield Record("unreachable", 0)
