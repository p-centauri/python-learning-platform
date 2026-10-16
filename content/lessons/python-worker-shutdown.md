## The idea in plain language

Graceful shutdown starts by stopping new work. It then gives work already admitted a chance to finish. It does not make an abrupt process kill safe or undo an independent consumer commit.

The lab's run function borrows a threading.Event. Before each new claim it checks whether that flag is set. Only one callback is admitted at a time, with at most the requested finite limit of claims. If the flag becomes set during a callback, that callback may finish acceptance and settlement, then no next claim begins.

The process fixture installs its SIGTERM handler only inside main, in the main thread, and restores the previous handler afterward. Importing the library does not change signal handlers. The handler requests stop; it does not open a Session, publish or migrate the database.

The parent waits to observe the child's actual callback admission, then sends SIGTERM to its owned process. The callback observes the stop flag, commits through the local consumer and returns acceptance. The child settles and exits normally. The saved report shows one admitted and settled event, while a second intent remains pending. This is a real signal/process check.

The fixture's publisher is cooperative. A blocking callback that never checks or returns can prevent graceful exit. SQL statement limits cannot terminate that callback. A process supervisor may eventually force termination; recovery then relies on the persisted lease and duplicate-safe consumer. This lab does not claim a hard shutdown deadline.

An already-set stop flag should admit no work and open no database connection. A stop arriving just after the admission check can still allow that claimed attempt: the stated boundary is the check before the claim. Describe this race honestly instead of promising instant cancellation.

## Worked example

This small local illustration explains one idea. It does not evaluate the database or process boundary; use the lab for that evidence.

```python
from threading import Event
stop = Event()
stop.set()
print(stop.is_set())
```

## Guided practice

A main-thread handler sets the borrowed flag. Accept and settle the cooperative callback. Return an actual finite report and release owned resources.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation, name the owner and time boundary, and explain one failure.

## Check your work

The flag gates new admission, with cooperative completion of current work. A cooperative flag and SQL limits cannot interrupt arbitrary Python callbacks. Label controlled timestamp fixtures and actual process observations separately.

Continue to [Build and review the leased worker lab](/lessons/python-worker-evidence).
