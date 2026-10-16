## The idea in plain language

A Future records a submitted job's state and eventual outcome. Before execution starts, cancel may stop it. Once it is running, cancel returns False: the computation continues. A completed future also cannot be cancelled. Cancelling is a scheduling request, not a rollback of effects.

future.result(timeout=...) limits how long the caller waits in that call. TimeoutError does not kill the worker. You must still arrange completion and let the pool owner shut down. In this example an Event coordinates a cooperative thread; the test/example deadline is not a hard worker execution limit.

shutdown(wait=True, cancel_futures=True) cancels jobs that are still queued and joins jobs that are already running. It can therefore wait after a failure. A with executor scope also waits on exit; it does not automatically mean queued jobs are cancelled. State the shutdown policy explicitly when cancellation matters.

Borrowed and owned pools need different treatment. A collector borrowing an executor must not close it. On failure it can attempt cancellation of the jobs it tracked, then re-raise. The owner still needs to join running work. The offload lab's outer run_batch function owns its dedicated pool and always waits before returning or raising.

Cooperative thread work can check a stop Event between safe steps, but a blocked or noncooperating operation can postpone stopping. Abrupt process termination can abandon cleanup and corrupt shared communication. The local lab uses orderly shutdown; it does not implement hard interruption, durable rollback or a hostile execution sandbox.

## Worked example

Save this trusted example as example.py and run it locally. Process startup requires a saved, guarded script.

```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Event
started, release = Event(), Event()
def work() -> int:
    started.set()
    if not release.wait(2):
        raise RuntimeError("example coordination deadline")
    return 7
with ThreadPoolExecutor(max_workers=1) as pool:
    future = pool.submit(work)
    try:
        assert started.wait(2)
        print(future.cancel())
        try:
            future.result(timeout=0.001)
        except TimeoutError:
            print("waiting ended; work continues")
    finally:
        release.set()
    print(future.result(timeout=2))
```

## Guided practice

Trace queued, running and completed states. Identify which deadline bounds caller waiting and where the worker actually completes.

## Independent practice

Use Events to demonstrate a running thread rejecting cancellation. Ensure release in finally and owner shutdown. Report the failure and cleanup trace without a speed claim.

## Check your work

A timeout/cancel request does not stop running work. Resource owners wait until their workers no longer use the resource.

Continue to [Bounded admission & ordered offload results](/lessons/python-bounded-executors).
