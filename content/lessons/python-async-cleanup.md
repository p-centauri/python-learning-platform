## The idea in plain language

An asynchronous resource may need to wait while closing. Calling its cleanup function creates an awaitable; that alone does not finish release. AsyncExitStack lets one async with scope register and await cleanup in reverse order. Use enter_async_context for an async context manager or push_async_callback for an awaitable cleanup function.

The lab borrows a synchronous iterable of async factories. Acquire one resource at a time by awaiting each factory. After a successful AsyncResource return, register aclose immediately before the next await. That avoids suspension between ownership handoff and registration. A factory owns partial work if it fails or is cancelled before returning.

Cancellation is a failure path, not permission to skip cleanup. Normal single task cancellation while the body awaits starts scope exit. Cooperative cleanup can still await and complete, after which cancellation propagates. Coordinate tests with Events so they know precisely when cancellation occurs; random sleeps are poor coordination.

These guarantees have limits. Repeated cancellation can interrupt cleanup. Stalled callbacks, forced termination or a closed event loop can prevent completion. shield changes cancellation behavior but is not a universal fix: any cleanup task still needs an owner to await its eventual outcome. The lab adds no shielding, indefinite wait policy, retries or hard deadlines.

The count bound limits successful handoffs, not elapsed time. Overflow observes one extra factory without invoking it. Cleanup failures retain native chaining and remaining-attempt behavior. Do not claim an unreturned partial resource was released by the scope; the factory must demonstrate that cleanup separately.

## Worked example

Run this trusted example locally and trace ownership and exit order.

```python
import asyncio
from contextlib import AsyncExitStack
events: list[str] = []
async def close(name: str) -> None:
    await asyncio.sleep(0)
    events.append(name)
async def main() -> None:
    async with AsyncExitStack() as stack:
        stack.push_async_callback(close, "a")
        stack.push_async_callback(close, "b")
        events.append("body")
    assert events == ["body", "b", "a"]
    print(events)
asyncio.run(main())
```

## Guided practice

Mark each await. Explain why cleanup registration immediately after acquisition has no intervening await.

## Independent practice

Implement owned_async_resources. Cancel after two handoffs using an Event, proving cleanup completes before cancellation escapes. Test cancellation during the next factory separately.

## Check your work

Cleanup is awaited in reverse order and cancellation propagates. Repeated cancellation or stalled code have explicit limits.

Continue to [ContextVars & request-local state](/lessons/python-context-state).
