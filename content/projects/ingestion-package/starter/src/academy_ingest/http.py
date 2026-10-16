from collections.abc import Iterator
from contextlib import contextmanager

import httpx

from .models import MAX_BODY_BYTES, Record


@contextmanager
def open_feed(
    url: str, *, client: httpx.Client, max_bytes: int = MAX_BODY_BYTES
) -> Iterator[Iterator[Record]]:
    """Own one response, borrow the client, close on every exit. See README."""
    raise NotImplementedError("Implement the managed HTTP boundary")
    yield iter(())
