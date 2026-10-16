from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import AsyncExitStack, aclosing, asynccontextmanager

import httpx

from .models import MAX_BODY_BYTES, FeedError, Record, Source, validate_source
from .parser import iter_records


@asynccontextmanager
async def open_feed(
    source: Source, *, client: httpx.AsyncClient, max_bytes: int = MAX_BODY_BYTES
) -> AsyncIterator[AsyncIterator[Record]]:
    validate_source(source)
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BODY_BYTES:
        raise FeedError("Invalid body byte limit")
    async with AsyncExitStack() as stack:
        try:
            response = await stack.enter_async_context(
                client.stream("GET", source.url, follow_redirects=False)
            )
        except httpx.HTTPError as exc:
            raise FeedError(f"HTTP failure: {type(exc).__name__}") from exc
        if response.status_code != 200:
            raise FeedError(f"feed status {response.status_code}")
        media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if media_type != "application/x-ndjson":
            raise FeedError("Expected application/x-ndjson")
        if response.headers.get("content-encoding", "identity").strip().lower() != "identity":
            raise FeedError("Compressed feeds are outside this lab contract")

        async def bounded_chunks() -> AsyncGenerator[bytes, None]:
            seen = 0
            try:
                async for chunk in response.aiter_raw(chunk_size=256):
                    seen += len(chunk)
                    if seen > max_bytes:
                        raise FeedError("feed exceeds body byte limit")
                    yield chunk
            except httpx.HTTPError as exc:
                raise FeedError(f"HTTP failure: {type(exc).__name__}") from exc

        async with aclosing(bounded_chunks()) as chunks, aclosing(iter_records(chunks)) as records:
            yield records
