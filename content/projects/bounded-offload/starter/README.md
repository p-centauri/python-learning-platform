# Bounded offload lab

Implement three functions in src/academy_bounded_offload/offload.py. The supplied frozen Job/Outcome types validate job descriptions. Import must create no pool, thread, I/O or output. Runtime is standard library only; Python 3.13+.

## Exact contract

- collect_ordered borrows executor, iterable and callable. Exact int pending is 1..4, limit is 0..16 (bool is rejected), checked before iterating/submitting. One iterator, one pass. Keep at most pending submitted-but-not-retired futures; completion alone does not retire a future. Fill the window before taking the oldest result; retire successful results in input order, then refill. Result is a tuple in input order, including when completion order differs.
- Limit bounds total accepted items. Detect overflow by observing item limit+1 without submitting it and without reading another item. Empty input at limit=0 succeeds. Never close borrowed input, shut down the borrowed pool, retry or return partial results. On input, submit or result failure, attempt cancel on all tracked futures and propagate the original exception within this local collector. Ordered waiting can postpone observing a later failure.
- cancel can stop queued work only. Running work may continue after collector failure. The pool owner must arrange completion and shutdown; cancelling is no rollback. No elapsed-time deadline is promised, including iterator/callable/file stalls.
- read_job is a top-level importable worker, accepting exact Job. Open its trusted absolute path inside the worker in binary mode; read exactly once with maximum 7 bytes. Accept only ASCII (0|[1-9][0-9]{0,4}) followed by one LF and value <=60000. Reject whitespace, CRLF, leading zeros, signs, extra data and invalid input with ValueError. Native opening errors propagate. Close on success and parsing failure. Return Outcome(id, value, actual PID, actual thread name, file_closed=True) after close.
- Job id is exact ASCII [a-z][a-z0-9-]{0,31}; path is exact absolute string, 1..512 characters. Paths name caller-owned local files, not a content snapshot. Keep files alive and stable until shutdown completes. No arbitrary URL, filesystem authorization, sandbox or hostile file guarantee is provided.
- run_batch validates settings, exact int workers=1..4 and exact mode string thread/process before source/pool access. It owns a fresh ThreadPoolExecutor (name prefix academy-offload) or ProcessPoolExecutor with explicit multiprocessing.get_context("spawn"). Pass read_job to collect_ordered, with pending/limit. Always shutdown(wait=True, cancel_futures=True) before successful return or failure propagation. Joining waits for running jobs, even on failure. Process arguments/results/exceptions cross serialization; same exception/object identity is not promised across that boundary.
- demo.py is a saved guarded script. Do not create process pools while importing modules, pass lambdas/live files/locks into a process pool, or let a worker wait on work from the same saturated pool.

## Work and evidence

1. Implement the collector, worker and owner. Use deterministic coordination rather than sleeps to describe cancellation. Add two regressions beyond the finite public suite.
2. Run tests, strict types, lint and the guarded demo. A test coordination deadline prevents a broken fixture from hanging; it does not impose a worker deadline.
3. Build a source archive and wheel. Install the real wheel into a fresh environment. Copy tests/demo outside source and remove PYTHONPATH/MYPYPATH. Never confuse an editable install with artifact evidence.
4. Report input order, admission peak, failure/cancel/shutdown traces and actual process PIDs. Explain shared-state locks, serialization/startup and build-specific GIL behavior. GIL-enabled CPython limits parallel Python bytecode in threads; I/O/native releases differ. Optional free-threaded builds still need correct shared-state synchronization. Do not promise speedup without measurements.
5. Compose outcomes with installed prior Row/Record/Snapshot packages; keep the file owner outside run_batch. Submit artifacts, actual output and tradeoffs for the four manual criteria. Academy does not execute this project or verify reported tests; these finite cases and manual judgments do not award mastery.

## Local commands

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m mypy src/academy_bounded_offload demo.py
.venv/bin/python -m ruff check src tests demo.py
.venv/bin/python demo.py
.venv/bin/python -m build
```

Threads share memory; processes have separate address spaces and serialize messages. Locks protect a chosen invariant, not arbitrary application correctness. No database writes, durable acknowledgments, recovery, performance claims or hard cancellation are implemented here.

Official references: [futures](https://docs.python.org/3.13/library/concurrent.futures.html), [multiprocessing](https://docs.python.org/3.13/library/multiprocessing.html), [threading](https://docs.python.org/3.13/library/threading.html), [free-threaded CPython](https://docs.python.org/3.13/howto/free-threading-python.html).
