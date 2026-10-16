## The idea in plain language

A worker count bounds how many jobs can run at once. It does not by itself bound how many futures or input items you submit. A huge list of submitted jobs can consume memory long before workers finish. Limit outstanding admission as well as worker count.

The lab's window contains submitted futures that have not yet been retired by the coordinating caller. A future can already be complete and still occupy that window. Fill up to pending, take the oldest result, retire it only after success, then admit the next item. This preserves input order even if workers finish in another order.

Ordered observation has a tradeoff. A slow first job can delay returning or observing a later error. This contract is not fail-fast. An unordered interface could use as_completed or wait, but would need a different result/error contract. State the behavior rather than silently changing order.

A separate total limit bounds accepted jobs. Observe one extra input item to detect overflow; do not submit it or keep reading. This consumes one extra item from borrowed input, so document that cost. Count limits do not interrupt a blocked iterator or callable. The lab never closes borrowed input or its borrowed executor.

Python 3.13 Executor.map collects inputs eagerly. Later Python versions offer different options, so do not assume a newer buffersize API on the baseline. The example below uses a rolling window with fixed trusted input. The full lab adds validation, overflow and failure cancellation while preserving ownership.

## Worked example

Save this trusted example as example.py and run it locally. Process startup requires a saved, guarded script.

```python
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from itertools import islice
def square(number: int) -> int:
    return number * number
source = iter(range(5))
with ThreadPoolExecutor(max_workers=2) as pool:
    window: deque[Future[int]] = deque(pool.submit(square, n) for n in islice(source, 2))
    values: list[int] = []
    while window:
        values.append(window[0].result())
        window.popleft()
        item = next(source, None)
        if item is not None:
            window.append(pool.submit(square, item))
print(values)
```

## Guided practice

Trace submitted, completed and retired separately. Explain the two-future peak and the slow-first-result tradeoff.

## Independent practice

Implement collect_ordered. Test one-pass borrowing, pending/limit bounds, the extra overflow observation, ordered errors, submit/input failure and queued-versus-running cancellation.

## Check your work

A worker count alone is not a submission bound. No retries, input closure, pool shutdown or partial report belong to this collector.

Continue to [Spawn, serialization & worker-owned resources](/lessons/python-process-startup).
