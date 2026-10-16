import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json

import httpx

from academy_async_feeds import BatchReport, Record, Source, ingest, open_feed


class DemoStream(httpx.AsyncByteStream):
    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b'{"id":"api","value":5}\n{"id":"worker","value":10}\n'

    async def aclose(self) -> None:
        pass


async def demo() -> BatchReport:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "application/x-ndjson"}, stream=DemoStream())

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:

        @asynccontextmanager
        async def configured(source: Source) -> AsyncIterator[AsyncIterator[Record]]:
            async with open_feed(source, client=client) as records:
                yield records

        return await ingest(
            [
                Source("feed-a", "https://example.test/a"),
                Source("feed-b", "https://example.test/b"),
            ],
            opener=configured,
        )


def main() -> None:
    print(json.dumps(asyncio.run(demo()), sort_keys=True))


if __name__ == "__main__":
    main()
