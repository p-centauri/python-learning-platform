## The idea in plain language

A spawned process starts a fresh interpreter and imports the program's main module. Put pool startup in main and call it under if __name__ == "__main__". Import must not start another pool. Save process examples as importable scripts; a REPL or python -c is not the same environment.

ProcessPoolExecutor needs serializable jobs, arguments and results. Use a top-level function with a stable import path. Lambdas, nested closures, locks and open files are unsuitable ordinary process messages. Pass a small job description and acquire the resource inside the worker instead.

Ordinary object identity does not survive serialization. A returned dataclass is a local reconstructed value, and a worker exception is transferred rather than the exact same exception object. Shared-memory APIs are separate mechanisms with their own synchronization and ownership rules; this unit does not introduce them.

The lab explicitly requests spawn rather than relying on platform/version defaults. Python 3.13 defaults differ across systems; newer versions also change defaults. Context choice is part of an application's contract. Libraries should avoid globally changing the process start method for unrelated callers.

A path is only a description. The caller owns the named temporary files and must keep them alive until workers are joined. Each worker opens/closes its own handle. Returning a value after close is useful; trying to return a live handle to the parent confuses both serialization and resource validity.

## Worked example

Save this trusted example as example.py and run it locally. Process startup requires a saved, guarded script.

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import os
def square(number: int) -> tuple[int, int]:
    return number * number, os.getpid()
def main() -> None:
    with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context("spawn")) as pool:
        futures = [pool.submit(square, n) for n in [2, 3]]
        results = [future.result() for future in futures]
    print([value for value, _ in results])
    print(all(pid != os.getpid() for _, pid in results))
if __name__ == "__main__":
    main()
```

## Guided practice

Run the saved script. Identify parent/worker import, top-level callable, copied integer arguments and distinct worker PIDs.

## Independent practice

Implement the spawned run_batch owner. Add a failing-worker case and prove the parent waits before deleting temporary input files. Explain why live handles are not messages.

## Check your work

Guard startup and state the explicit context. Acquire inside the worker and join before the caller releases file ownership.

Continue to [GIL behavior depends on the interpreter build](/lessons/python-gil-builds).
