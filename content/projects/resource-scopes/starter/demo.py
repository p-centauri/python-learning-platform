import asyncio
import json
from academy_resource_scopes import (
    AsyncResource,
    Resource,
    current_request,
    owned_async_resources,
    owned_resources,
    request_scope,
)

events: list[str] = []


def acquire(name: str) -> Resource[str]:
    events.append("open:" + name)

    def close() -> None:
        events.append("close:" + name)

    return Resource(name, close)


async def async_acquire() -> AsyncResource[str]:
    events.append("open:async")

    async def close() -> None:
        await asyncio.sleep(0)
        events.append("close:async")

    return AsyncResource("async", close)


async def main() -> None:
    with request_scope("demo"):
        with owned_resources([lambda: acquire("a"), lambda: acquire("b")]) as values:
            label = current_request()
            assert values == ("a", "b")
        async with owned_async_resources([async_acquire]) as values_async:
            assert values_async == ("async",)
    print(json.dumps({"label": label, "restored": current_request(), "events": events}))


asyncio.run(main())
