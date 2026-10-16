## The idea in plain language

An invariant is a rule that must remain true while state changes. For two balances, a transfer should preserve their sum. Updating one balance and then the other is several steps, even if each assignment looks small. A second thread could observe an incomplete change.

A Lock lets cooperating threads agree on a critical section. Hold it around the complete transfer, and use the same lock when reading the related balances. Protecting only writes while readers ignore the lock does not give readers the same guarantee. A lock belongs to an invariant, not merely a convenient line of code.

Use with lock so ordinary exceptions release it. Keep the section short. Calling arbitrary callbacks, blocking on another future or taking several locks in inconsistent order can introduce deadlock. Locks are not automatic error recovery: if code changes one balance and raises before changing the other, you still need an explicit update/rollback design.

The GIL does not establish your application's multi-step rules. Optional free-threaded builds make correct synchronization especially visible, and native work may also release the GIL. Do not rely on one observed scheduling order. Deterministic event traces can explain an interleaving, while a stress test passing does not prove the absence of every race.

Prefer returned immutable messages and owner-side aggregation when shared mutable state is unnecessary. The offload lab returns values in a tuple; its collector is coordinated by one calling thread. It does not make arbitrary input iterators, callbacks or shared executors universally thread-safe.

## Worked example

Save this trusted example as example.py and run it locally. Process startup requires a saved, guarded script.

```python
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
class Balances:
    def __init__(self) -> None:
        self._lock = Lock()
        self._left = 100
        self._right = 0
    def transfer(self, amount: int) -> None:
        with self._lock:
            self._left -= amount
            self._right += amount
    def snapshot(self) -> tuple[int, int]:
        with self._lock:
            return self._left, self._right
balances = Balances()
with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(balances.transfer, 1) for _ in range(10)]
    for future in futures:
        future.result()
print(balances.snapshot())
```

## Guided practice

Identify the sum invariant. Explain why snapshot and transfer use the same lock, and why a callback inside the lock could change the risk.

## Independent practice

Write a deterministic lost-update trace and a guarded fix. Describe exception handling and lock order. Prefer owner-side aggregation for independent returned outcomes.

## Check your work

Guard the complete invariant and its readers. Explain what locks cannot prove or repair.

Continue to [Future cancellation, waiting & worker shutdown](/lessons/python-future-lifetime).
