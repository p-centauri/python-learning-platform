## The idea in plain language

Complete three functions: collect_ordered borrows a pool and a one-pass source, read_job opens/closes a worker-local file, and run_batch owns a dedicated pool through shutdown. These separate responsibilities make failure easier to explain.

The collector bounds submitted-but-not-retired jobs and total accepted input. It preserves input order, attempts queued cancellation on failure and never closes borrowed owners. A running job may continue after collector failure. run_batch therefore waits before returning or propagating failure, even if that delays the caller.

Each immutable Job carries an id and a trusted local absolute path. The caller keeps files alive and stable; the worker reads at most seven bytes and closes its own handle before returning an Outcome. The path is neither a content snapshot nor filesystem authorization. FIFO observation, count bounds and frozen dataclasses do not establish hard deadlines or tamper resistance.

Use the guarded demo to prove thread PIDs match the parent and process PIDs differ. Test actual spawned workers, parsing failures, finite admission, overflow and responsible shutdown. Also use controlled Future states to reproduce queued cancellation and already-running work; do not rely on sleeps to make a race happen.

Build a real source archive and wheel. Install freshly, copy tests/demo outside source and run without editable paths. Compose returned outcomes with earlier installed Row/Record/Snapshot values while the file owner remains outside the batch owner. Report actual output, two new regressions and build-specific GIL facts.

Four manual criteria review admission/borrowing, failure/shutdown, process/resource boundaries and installed evidence. Academy stores your reported evidence; it does not execute this project or independently verify it. Measured profiling/cache behavior, PostgreSQL/FastAPI persistence, durable worker recovery and applied AI remain later units.

## Worked example

Save this trusted example as example.py and run it locally. Process startup requires a saved, guarded script.

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from pathlib import Path
from tempfile import TemporaryDirectory
def read_value(path: str) -> tuple[int, bool]:
    with Path(path).open("rb") as stream:
        raw = stream.read(7)
    return int(raw), stream.closed
def main() -> None:
    with TemporaryDirectory() as directory:
        paths: list[str] = []
        for index, value in enumerate([5, 10]):
            path = Path(directory) / str(index)
            path.write_bytes(str(value).encode("ascii") + b"\n")
            paths.append(str(path))
        with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context("spawn")) as pool:
            futures = [pool.submit(read_value, path) for path in paths]
            results = [future.result() for future in futures]
        print([value for value, _ in results])
        print(all(closed for _, closed in results))
if __name__ == "__main__":
    main()
```

## Guided practice

Trace caller-owned named files, worker-owned handles, borrowed collector and owned pool. Identify which actions can continue after a failure.

## Independent practice

Complete the downloadable lab, add two regressions and install its wheel cleanly. Submit actual admission/cancellation/PID traces, strict types and prior-value composition.

## Check your work

Finite tests and reported manual evidence remain distinct from objective learner grading and mastery. Explain latency and shutdown limits.

[Download the bounded offload starter](/api/projects/python-bounded-offload/starter), then open the [project checklist](/projects#python-bounded-offload) and [submission workspace](/projects/python-bounded-offload/submissions).

Continue to [Measure a workload before optimizing](/lessons/python-measurement-baselines).
