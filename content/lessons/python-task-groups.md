## The idea in plain language

A task schedules a coroutine on the running loop. When several tasks belong to one operation, give them an owner. An asyncio.TaskGroup owns the tasks created through it and waits for them when its async context exits. The caller cannot report success while an owned task is still working.

If a child raises an ordinary exception, the group cancels its remaining related tasks and waits for them to finish. It then raises an ExceptionGroup containing the uncaught failures. Cancellation is cooperative, so cleanup must still run and a blocked synchronous function can still delay exit. Keep failures as a group; selecting only the first message can hide a second failure that matters.

The except* syntax handles matching leaves of a group. It does not turn grouped errors into one ordinary exception, and unhandled leaves still propagate. This lesson uses a simple ValueError example; the project preserves the complete group for its caller rather than converting failures into a success dictionary.

Child cancellation has a different meaning from an ordinary child failure. A child that ends with CancelledError is not by itself treated as an ordinary failure by TaskGroup. Therefore group exit alone cannot prove a business operation completed every requested source. The project checks that all expected source outcomes exist before returning. KeyboardInterrupt and SystemExit also receive special handling; do not claim all BaseException behavior is identical.

## Worked example

Run this example locally and explain each observed result.

```python
import asyncio

async def broken() -> None:
    raise ValueError("invalid source")

async def main() -> None:
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(broken())
    except* ValueError as errors:
        print(type(errors).__name__, len(errors.exceptions))  # ExceptionGroup 1

asyncio.run(main())
```

## Guided practice

Add a sibling that waits on an Event and records a finally cleanup flag. Verify the ordinary failure cancels it and the group exits only after that flag is recorded. Avoid sleeps as a guess about which task has started.

## Independent practice

Create two deterministic failing tasks and inspect matching leaves with except*. Explain which unmatched failures still escape. Then show why a child-only cancellation requires an explicit completion check in the batch contract.

## Check your work

Every created task belongs to an owner, and no success is returned before group exit. Your explanation distinguishes ordinary grouped failure, caller cancellation and child-only cancellation.

Continue to [Cancellation & reliable async cleanup](/lessons/python-cancellation).
