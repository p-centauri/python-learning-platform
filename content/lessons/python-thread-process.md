## The idea in plain language

Concurrency means work overlaps. Parallelism means work executes at the same time. A thread belongs to its process and shares ordinary application memory with other threads. A separate process has its own address space; ordinary messages pass through serialization rather than shared Python object identity.

Threads are often useful while waiting for files, sockets or other external work. On an ordinary GIL-enabled CPython build, multiple threads do not run Python bytecode in parallel within one interpreter. Some native libraries release the GIL during computation. Processes can run Python work in separate interpreters, but startup, serialization and communication cost time and memory.

Choose based on the actual job and environment. A small calculation may be slower in either pool because scheduling costs more than the work. This example demonstrates identity and ordering, not speed. Profiling comes in the next unit; there is no speedup promise here.

A pool has an owner. That owner decides admission, observes results, handles failure and joins workers before releasing resources they need. Passing an existing pool borrows it; creating a dedicated pool makes you responsible for shutdown. Workers should not submit work and wait for it in the same saturated pool: every available worker may be waiting for a job that cannot start.

## Worked example

Save this trusted example as example.py and run it locally. Process startup requires a saved, guarded script.

```python
from concurrent.futures import ThreadPoolExecutor
import os
def work(number: int) -> tuple[int, int]:
    return number * number, os.getpid()
with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(work, n) for n in [2, 3]]
    values = [future.result() for future in futures]
print([value for value, _ in values])
print(all(pid == os.getpid() for _, pid in values))
```

## Guided practice

Trace shared process identity and input-order observation. Explain why this example proves no performance benefit.

## Independent practice

Compare an I/O wait job and a pure Python CPU job. Document interpreter/build, workload size, data transfer and pool owner; defer speed claims until measured.

## Check your work

Choose a boundary based on work and ownership. A worker cannot safely wait on jobs trapped behind itself in an exhausted pool.

Continue to [Shared state, locks & invariants](/lessons/python-thread-state).
