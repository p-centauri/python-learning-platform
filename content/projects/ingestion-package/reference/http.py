from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from urllib.parse import urlsplit

import httpx

from .models import MAX_BODY_BYTES, FeedError, Record
from .parser import iter_records


@contextmanager
def open_feed(
    url: str, *, client: httpx.Client, max_bytes: int = MAX_BODY_BYTES
) -> Iterator[Iterator[Record]]:
    try:
        parts = urlsplit(url)
        valid = (
            parts.scheme == "https" and parts.hostname and not parts.username
            and not parts.password and not parts.fragment and parts.port in (None, 443)
            and not any(c.isspace() or ord(c) < 32 for c in url)
        )
    except ValueError:
        valid = False
    if not valid:
        raise FeedError("Use a trusted HTTPS URL without credentials, fragment or nonstandard port")
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BODY_BYTES:
        raise FeedError("Invalid body byte limit")
    with ExitStack() as stack:
        try:
            response = stack.enter_context(client.stream("GET", url, follow_redirects=False))
        except httpx.HTTPError as exc:
            raise FeedError(f"HTTP failure: {type(exc).__name__}") from exc
        if response.status_code != 200:
            raise FeedError(f"feed status {response.status_code}")
        media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if media_type != "application/x-ndjson":
            raise FeedError("Expected application/x-ndjson")
        encoding = response.headers.get("content-encoding", "identity").strip().lower()
        if encoding != "identity":
            raise FeedError("Compressed feeds are outside this lab contract")

        def bounded_chunks() -> Iterator[bytes]:
            seen = 0
            try:
                for chunk in response.iter_raw(chunk_size=256):
                    seen += len(chunk)
                    if seen > max_bytes:
                        raise FeedError("feed exceeds body byte limit")
                    yield chunk
            except httpx.HTTPError as exc:
                raise FeedError(f"HTTP failure: {type(exc).__name__}") from exc

        records = iter_records(bounded_chunks())
        try:
            yield records
        finally:
            records.close()
