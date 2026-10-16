## The idea in plain language

Concurrent tests need to know what has happened before they trigger the next action. An Event can record that a worker entered a read or acquired a resource. Wait for that event, request cancellation or inject a failure, then await the job and inspect cleanup. A fixed sleep only guesses about scheduler timing and can become flaky on a slower machine.

Use a watchdog to fail a test that deadlocks. Keep it separate from the deadline behavior being tested: the job's timeout is the contract, while an outer wait_for protects the test harness. Assert the outcome and observed cleanup rather than an exact elapsed duration. A blocked Event makes deadline behavior reproducible without relying on a live remote service.

Test the actual composition. Keep the real bounded worker and HTTP owner, use an observable fake transport, and assert totals only after all source contexts finish successfully. Include a valid record followed by invalid input, sibling cancellation, caller cancellation, a cleanup error and a child-only cancellation. A passing happy-path sum does not prove these shutdown boundaries.

This is a local in-memory batch report, not a durable worker or transaction. Source side effects inside injected callbacks cannot be rolled back by TaskGroup. The project performs no database writes, retries or success publication to an external system. Those later boundaries need PostgreSQL and recovery evidence, and the complete advanced/backend/applied AI paths remain planned.

## Worked example

Run this example locally and explain each observed result.

```python
import asyncio

async def main() -> None:
    entered, release = asyncio.Event(), asyncio.Event()
    outcomes: list[int] = []
    async def work() -> None:
        entered.set()
        await release.wait()
        outcomes.append(10)
    async with asyncio.TaskGroup() as group:
        group.create_task(work())
        await entered.wait()
        print(outcomes)  # []: the worker is known to be waiting
        release.set()
    print(outcomes)  # [10]: owned work is complete

asyncio.run(main())
```

## Guided practice

Download the lab and implement its three functions. Run all public cases, strict types and lint. Compare the worker/task limit assertion with merely placing a semaphore around already-created source tasks.

## Independent practice

Add two meaningful failure/cancellation regressions, build and install the wheel outside source, and connect the earlier selector through a typed async opener. Submit your repository/artifact, reported tests, ownership/budget reasoning and known gaps for manual review.

## Check your work

You can explain which component each fake replaces, what the watchdog proves and why no returned report may represent a partial batch. All seventy-five public cases are finite checks, not certification; review/checklist evidence remains separate from mastery.

Open the [Bounded async feed-ingestion lab](/projects#python-async-feeds) and submit evidence for manual review. Object behavior, advanced typing and context/resource lifetime are published next; concurrency/measurement and backend persistence remain planned.

Continue to [Attribute lookup & missing values](/lessons/python-attribute-lookup) for the next published Python unit.
