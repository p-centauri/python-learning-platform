## The idea in plain language

An HTTP timeout can limit a connect, read, write or pool-wait operation. It does not automatically limit the total time of a job with several sources, queue waits and cleanup. A sequence of individually acceptable waits can still exceed the budget a caller intended.

Wrap the related job in asyncio.timeout to give it one cooperative time budget. The context cancels its current task when that budget expires and converts its own cancellation into TimeoutError as the context exits. Catch that error outside the timeout context. Caller cancellation is still a separate outcome; do not rewrite every CancelledError as a timeout.

For absolute budgets, asyncio.timeout_at uses the event loop's monotonic clock rather than calendar time. The remaining budget should not restart after each chunk or retry. A retry policy is deliberately outside this lab; introducing one later requires explicit attempt limits and time accounting.

A timeout is not a hard execution deadline. The task must reach cooperative waits, and TaskGroup shutdown waits for child cleanup. Blocking calls or code that swallows cancellation can overrun the intended budget. Our deterministic tests block on Events and assert TimeoutError plus closure. They do not claim an exact wall-clock duration or prove protection from hostile code. The isolated coding runner is a separate resource boundary.

## Worked example

Run this example locally and explain each observed result.

```python
import asyncio

async def main() -> None:
    try:
        async with asyncio.timeout(0):
            await asyncio.Event().wait()
    except TimeoutError:
        print("expired")

asyncio.run(main())
```

## Guided practice

Explain why the handler is outside the context. Draw one budget spanning queue admission, source opening, reading and group shutdown. Separate it from the AsyncClient connect/read settings.

## Independent practice

Use an Event that never releases to test an overall deadline without relying on a live service. Record cleanup in finally and assert it after TimeoutError. Explain why a wall-clock assertion within a few milliseconds would be fragile.

## Check your work

You can identify which timeout owns an error and where it is converted. The example uses the standard library’s zero budget; the lab’s configured budget must be positive and at most 30 seconds. Neither establishes a hard kill limit.

Continue to [Bounded queues & fixed workers](/lessons/python-bounded-queues).
