## The idea in plain language

An async def function creates a coroutine object when called. Its body does not automatically start. Await the object to run it as part of the current task, or schedule it as a task when you want related operations to make progress together. A coroutine object is normally awaited once; create a fresh one for another invocation.

The event loop coordinates tasks. While a task waits for asynchronous I/O, another ready task can run. This is cooperative concurrency, not an instruction to run Python CPU work in parallel. A long calculation or time.sleep inside an async function still blocks that loop thread. Writing async before a function name cannot make a synchronous HTTP client asynchronous.

Await means wait for an awaitable result. It can suspend the current task, but it is not guaranteed to do so: an operation that is already ready may complete immediately. Two consecutive await calls can still be sequential. You need a deliberate task structure to overlap independent work.

Use asyncio.run once at the outer entry of a normal CLI. It creates and closes the loop for that call. Inside an already running async application, await the coroutine instead of trying to start a nested loop. Our API still does not execute learner code; these examples and the project run locally.

## Worked example

Run this example locally and explain each observed result.

```python
import asyncio

async def read_value() -> int:
    return 10

async def main() -> None:
    value = await read_value()
    print(value)  # 10

asyncio.run(main())
```

## Guided practice

Trace creation, awaiting and return in the example. Move the print into read_value and explain why merely creating its coroutine does not produce the print. If experimenting with an unused object locally, close it so you do not leave a warning-producing coroutine.

## Independent practice

Write two small asynchronous operations and await them sequentially. Explain which behavior would change when scheduling tasks, and which would stay unchanged for a long synchronous calculation. Use a fresh coroutine object for each call.

## Check your work

You can distinguish the function, its coroutine object and a task. You can choose a CLI entry or an existing async entry without nesting asyncio.run. Observed overlap does not establish CPU parallelism.

Continue to [Task groups & related failures](/lessons/python-task-groups).
