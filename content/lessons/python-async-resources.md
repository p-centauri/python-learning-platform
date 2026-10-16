## The idea in plain language

An async iterator supplies values through asynchronous next operations. Async for waits for those values one at a time. It supports a lazy stream whose next chunk may require I/O. The iterator protocol alone does not promise ownership or an aclose method; an async generator has additional close behavior.

An async context manager describes lifetime: enter, use, then await exit cleanup. Use async with for an owned HTTP response and contextlib.aclosing for an owned async generator. Leaving a loop early is not enough evidence that every borrowed or owned asynchronous resource has closed at the right time.

The parser borrows its chunk input. Closing the parser must not close a caller's borrowed source. The HTTP adapter has a different role: it creates the response, its bounded chunk generator and the parser, so it owns those resources and closes them in reverse order. The application owns the AsyncClient and can reuse it across requests.

Type the interface accurately. AsyncIterator describes iteration, while AsyncGenerator also supports explicit close operations. The reference uses the latter where an aclosing context needs it. This is a useful connection to the earlier protocol lessons: a type should state the operations an owner needs, rather than hiding missing behavior with a cast. Cleanup after partial setup still needs a clear owner; AsyncExitStack can release resources already acquired before a later step fails.

## Worked example

Run this example locally and explain each observed result.

```python
import asyncio
from collections.abc import AsyncGenerator
from contextlib import aclosing

closed: list[bool] = []
async def readings() -> AsyncGenerator[int, None]:
    try:
        yield 10
        yield 20
    finally:
        closed.append(True)

async def main() -> None:
    async with aclosing(readings()) as rows:
        print(await anext(rows))  # 10
    print(closed)  # [True]

asyncio.run(main())
```

## Guided practice

Compare the parser’s borrowed chunk source with the HTTP adapter’s owned generator. Stop after one record and verify which close methods run. Use the public early-exit test instead of waiting for process termination.

## Independent practice

Write an async context manager that acquires two cooperative resources. Make the second setup fail and demonstrate that the first is closed. Explain why the caller’s shared client must remain open.

## Check your work

You can draw the ownership chain and distinguish next-value waiting from resource lifetime. Your annotations include close support where needed, and tests observe early-exit and failure cleanup without relying on garbage collection.

Continue to [Async HTTP streams & shared clients](/lessons/python-async-http).
