# ADR 0022: bounded offload and worker ownership

Date: 2026-10-03. Status: accepted.

## Context

Step 6 needs threads/processes after context/resource lifetime. Worker count is not a submission bound; wait timeouts and cancellation are often mistaken for termination. Spawned workers need explicit startup/serialization and local resource ownership. Interpreter version does not establish the build or current GIL state.

## Decision

Publish seven lessons with simple runnable examples: execution models, shared-state invariants/locks, future lifetime, bounded admission, spawned processes, build/runtime GIL reporting and installed evidence. A separate Python offload contracts skill preserves earlier scenario denominators. Catalog 2026.10-offload-v1 adds fourteen scenarios; interactive/recall/rubric content advances to v8. Existing exams and fixed learner histories stay unchanged.

Use academy-bounded-offload-lab 0.1.0, Python 3.13+, standard-library runtime. Three unfinished functions separate borrowing from ownership:
- collect_ordered borrows an executor and a one-pass input, admitting at most pending submitted-but-not-retired futures. Successful oldest results retire in input order before refill. Completed but unobserved futures still occupy the window.
- read_job is a top-level importable worker. It opens a trusted local path inside the worker, reads at most seven bytes once, validates canonical LF-terminated decimals 0..60000 and closes before returning an immutable Outcome with actual process/thread identity.
- run_batch owns a dedicated thread pool or explicit spawn process pool. It always shutdowns with wait=True and cancel_futures=True before returning or propagating failure.

Validate exact integers pending/workers 1..4 and total limit 0..16 before source/pool access. Observe one overflow item without submitting it or reading another. Never close borrowed input/executor, retry or return a partial report. On collector failure, attempt cancellation of tracked futures and propagate the local original exception. Input-order observation can delay later failures; no fail-fast promise.

Cancellation cannot stop already running futures. result(timeout) bounds caller waiting only. The owning batch joins running work even after failure, so its return/failure has no hard deadline. No rollback or durable acknowledgment is implemented. Caller-owned named files must remain alive and stable until shutdown; copied paths are not snapshots. Process arguments/results/errors cross serialization, without same-object/exception identity promises.

Guard process startup in an importable saved main script; use top-level workers and serializable messages rather than lambdas/live handles/locks. Do not globally change unrelated start methods. Threads share memory; locks protect complete cooperating application invariants, including readers. Passing a stress test is not exhaustive race proof.

Report implementation/build and optional runtime GIL probe separately. Ordinary GIL-enabled CPython restricts parallel Python bytecode; waiting/native extensions differ. Optional free-threaded builds can have the GIL enabled and still require correct shared-state synchronization. The unit promises no speedup; measurement follows next.

The authenticated nine-file ZIP excludes references/private grading keys. The API serves bytes and stores manual evidence, never importing or executing learner packages. Trusted maintainer subprocesses verify 66 public cases, examples, strict types/lint, source/wheel contents and installed prior-package composition. Test coordination deadlines prevent broken fixtures hanging; they are not execution limits.

Four criteria review admission/borrowing, failure/shutdown, process/resource/build boundaries and installed evidence. Reported learner tests and manual judgments remain distinct from isolated objective checks and mastery.

## Consequences and limits

One bounded advanced unit is delivered; step 6 and full expertise remain open. Trusted local files and normal cooperative shutdown are assumed. Count/byte limits cannot interrupt blocked iterators, files or callables; process pools are not hostile-code isolation. No database persistence, worker recovery or academy schema/runtime dependency change is included. CI is configured; remote execution remains unobserved.

Next: measured profiling/allocation/cache behavior and library evolution, then PostgreSQL/FastAPI persistence, durable workers/deployment and applied AI.

References: [futures](https://docs.python.org/3.13/library/concurrent.futures.html), [multiprocessing](https://docs.python.org/3.13/library/multiprocessing.html), [threading](https://docs.python.org/3.13/library/threading.html), [free-threaded CPython](https://docs.python.org/3.13/howto/free-threading-python.html).
