## The idea in plain language

A queue separates producing work from consuming it. Set a positive maxsize so an await queue.put waits when the queue is full. That wait is backpressure: it tells the producer to slow down instead of holding an unlimited backlog. A maxsize of zero means unbounded capacity, not a queue that accepts nothing.

Queue capacity and active task count are different limits. Creating one task for every source and putting a semaphore around the HTTP call limits active requests, but still creates all those waiting tasks. A fixed worker pool with one producer bounds both the number of tasks and the pending queue. The lab also caps the input configuration to sixteen sources.

Each successful queue.get increases the responsibility to call task_done once. Use finally so accounting stays balanced when processing fails. Queue.join waits for the unfinished-work counter to reach zero; it does not validate your results or guarantee durable storage. This queue belongs to one local run and disappears after a failure. A durable worker needs additional persistence and recovery rules later.

Normal completion needs an explicit stop signal. After sending all sources, the producer sends one None sentinel for each worker. A worker recognizes its sentinel, accounts for that get and exits. The enclosing TaskGroup waits for all workers. On ordinary failure the group cancels the producer and siblings, so it does not rely on successfully sending every normal sentinel.

## Worked example

Run this example locally and explain each observed result.

```python
import asyncio

async def main() -> None:
    queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=1)
    async def produce() -> None:
        await queue.put(7)
        await queue.put(None)
    async def consume() -> None:
        while True:
            item = await queue.get()
            try:
                if item is None:
                    return
                print(item)  # 7
            finally:
                queue.task_done()
    async with asyncio.TaskGroup() as group:
        group.create_task(produce())
        group.create_task(consume())
    await queue.join()

asyncio.run(main())
```

## Guided practice

Trace a full one-item queue and the producer waiting for room. Count producer, worker and job tasks separately from queued Source objects. Explain why the sentinel must also receive task_done.

## Independent practice

Implement a fixed two-worker pool over sixteen sources with queue size one. Use Events to block active work and an observable queue to measure capacity and task count. Release the work, then verify totals and normal completion without leaking tasks.

## Check your work

The limit is applied before creating work, not only around the HTTP call. Your queue has positive capacity, every successful get is balanced, and the stop protocol covers normal completion while TaskGroup covers failure shutdown.

Continue to [Async iteration & context ownership](/lessons/python-async-resources).
