## The idea in plain language

HTTPX AsyncClient exposes awaitable network operations. Reuse one application-owned client across related requests so its connection pool has a meaningful lifetime. Creating a new client inside a hot per-record loop loses that reuse and scatters cleanup responsibility. A normal synchronous Client is still blocking when called from async code.

Use async with client.stream to own a streaming response. Read raw bytes with aiter_raw, then frame records separately. A network chunk is not a JSON record: it may contain part of a line, several lines, or the end of one record and the beginning of another. The new lab keeps the earlier strict ID/value shape and inclusive framing limits, with a separately typed async implementation.

Enforce response policy before consuming records: status, media type, disabled redirects and identity encoding. Count actual processed body bytes; Content-Length is only a header claim. Limits on parser pending bytes do not establish a hard bound on transport or socket buffering. URL syntax also does not decide which destination is trusted, so the local lab takes configured sources rather than offering a public fetch endpoint.

Keep error boundaries precise. An HTTP acquisition or read failure may become FeedError with its original cause. A consumer's own exception should escape unchanged, even if it happens to be an HTTPX error. Put handlers around the operations you own, not around a context yield that also executes caller code. Cancellation still needs owned response cleanup and a borrowed client that remains reusable.

## Worked example

Run this example locally and explain each observed result.

```python
import asyncio
from collections.abc import AsyncIterator
import httpx

class Bytes(httpx.AsyncByteStream):
    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b"10\n"
    async def aclose(self) -> None:
        pass

async def main() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=Bytes())
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        async with client.stream("GET", "https://example.test/feed") as response:
            body = b"".join([chunk async for chunk in response.aiter_raw()])
            print(body.decode().strip())  # 10
        print(client.is_closed)  # False; the application still owns it

asyncio.run(main())
```

## Guided practice

The tiny example joins a fixed three-byte fake body only to show the API. Explain why the actual lab must stream and bound input instead. Implement source validation and response policy before yielding a parser to the caller.

## Independent practice

Use MockTransport with an observable AsyncByteStream. Cover early exit, a read failure, caller exception identity, an incorrect Content-Length and cancellation while reading. Reuse the same client after the first response closes.

## Check your work

Your test keeps the actual owner and parser real while controlling the transport. It verifies response closure without claiming live DNS/TLS behavior, SSRF protection or a hard allocation limit.

Continue to [Deterministic shutdown & the async lab](/lessons/python-async-tests).
