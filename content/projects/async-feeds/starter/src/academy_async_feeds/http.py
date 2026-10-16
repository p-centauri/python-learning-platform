from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from .models import MAX_BODY_BYTES, Record, Source


@asynccontextmanager
async def open_feed(
    source: Source, *, client: httpx.AsyncClient, max_bytes: int = MAX_BODY_BYTES
) -> AsyncIterator[AsyncIterator[Record]]:
    """Own the response and parser, borrow the client; see README."""
    raise NotImplementedError("Implement the async HTTP owner")
    yield _empty()


async def _empty() -> AsyncIterator[Record]:
    return
    yield Record("unreachable", 0)
