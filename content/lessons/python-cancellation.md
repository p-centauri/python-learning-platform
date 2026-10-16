## The idea in plain language

Cancelling a task requests that it stop. The request normally becomes CancelledError at the next opportunity for asynchronous waiting. It is not a command that instantly destroys the task, and it cannot interrupt arbitrary blocking code in the same loop thread.

Put owned cleanup in finally blocks or async context managers. The caller cancelling a job should await that job so it can observe completion of the cleanup. Asking for cancellation and immediately returning can leave open responses or unfinished work behind.

CancelledError inherits directly from BaseException. An except Exception handler normally does not catch it. If you catch it deliberately, clean up and re-raise. Swallowing it can break the shutdown behavior of TaskGroup and timeout contexts, both of which use cancellation internally. Do not add uncancel or shield as a general fix; each changes the ownership story and needs a separate justified contract.

Ownership remains important during failure. A helper closes the response it created while preserving a borrowed AsyncClient for the application. Do not depend on garbage collection to close an async generator promptly. Async cleanup may itself await, so the lab assumes cooperative resources. A second cancellation or uncooperative cleanup can complicate shutdown; this unit is not a hard kill boundary for hostile code.

## Worked example

Run this example locally and explain each observed result.

```python
import asyncio

async def main() -> None:
    entered = asyncio.Event()
    closed: list[bool] = []
    async def work() -> None:
        try:
            entered.set()
            await asyncio.Event().wait()
        finally:
            closed.append(True)
    task = asyncio.create_task(work())
    await entered.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print(closed)  # [True]

asyncio.run(main())
```

## Guided practice

Trace why the example waits for entered before cancelling. Move the cleanup assertion after await task. Compare it with a caller that invokes cancel but never awaits the task; explain what evidence that caller is missing.

## Independent practice

Create a fake owned stream that records aclose and a borrowed client that records its own lifetime. Cancel a consumer after it enters a blocked read. Assert the stream is closed and the client remains available.

## Check your work

Cancellation remains visible to the caller and cleanup is observed before the operation is considered finished. You can explain the difference between a cancellation request and a hard resource/time limit.

Continue to [Operation timeouts & total deadlines](/lessons/python-async-deadlines).
