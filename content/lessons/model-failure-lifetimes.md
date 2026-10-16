A timeout means the caller did not obtain a usable result within its waiting policy. It does not prove that the remote provider performed no work or that any billable work was cancelled. An exception can also arrive after work started. Treat these outcomes as uncertain instead of silently returning an empty success or immediately sending the same request again. The local lab stops on timeout, provider failure or invalid response; it supplies no automatic retry policy.

One monotonic deadline begins after preflight and covers the bounded provider-call loop. Before each call, compute the remaining time from that same deadline. Giving every call the original timeout would expand the run's total waiting budget. The tests inspect a two-call sequence to confirm the budget shrinks rather than resets. The example below shows awaited cancellation cleanup, while the installed timeout fixture observes actual entered and finished events.

An async timeout works by cooperative cancellation. The provided WaitingTransport suspends until cancelled, then awaits its finally cleanup and marks completion. The run observes that cleanup before reporting timeout. External CancelledError propagates to the caller after cleanup; it is not swallowed as a provider-error report. The adapter borrows its transport, so ending a call does not close unrelated owner resources. Reuse the scripted transport in another run to verify that boundary.

Cooperation has limits. Blocking code, a coroutine that suppresses cancellation, repeated cancellation or slow cleanup can exceed the waiting policy. Synchronous preflight and parsing are not hard interrupted, and already-buffered transport bytes are not a hostile network memory guarantee. External cancellation produces no saved local report or durable ledger. A real system needs persistent reconciliation, provider request identity and accounting before deciding whether to retry uncertain work. The next lesson explains why this finite local ledger retains the worst-case reservation when usage is unknown.

## Guided practice

Predict the printed result, then describe the part of the real model boundary that this small illustration leaves untested.

```python
import asyncio

async def work(closed: list[str]) -> None:
    try:
        await asyncio.Event().wait()
    finally:
        await asyncio.sleep(0)
        closed.append("closed")

async def main() -> None:
    closed: list[str] = []
    task = asyncio.create_task(work(closed))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    print(closed[0])

asyncio.run(main())
```

## Independent practice

Run the waiting timeout and external-cancellation fixtures. Verify entered/finished events, propagated cancellation, borrowed transport reuse and a shrinking deadline across calls.

## Check your work

Do not claim that cooperative cleanup rolls back remote effects or that timeout means zero usage. State the absence of a durable cancellation ledger and hard interruption.

Use the [Model contracts project](/projects#model-contracts). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
