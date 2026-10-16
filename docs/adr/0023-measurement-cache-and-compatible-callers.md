# ADR 0023: finite measurement, bounded cache and compatible callers

Date: 2026-10-04. Status: accepted.

## Context

Step 6 needs measured profiling/allocation/cache work after threads/processes. Timings vary with environment and state; current/peak traced allocation is not total RSS. Cache key omissions or indefinite references can change correctness. Interface evolution must preserve supported caller behavior, not only internal tests.

## Decision

Publish eight lessons: baseline/clock choice, profiler self/cumulative cost, input growth/materialization, allocation ownership, complete cache keys, LRU/failure lifetime, compatible interfaces and installed evidence. Use a separate Python measurement contracts skill, catalog 2026.10-measurement-v1 and interactive/recall/rubric v9. Sixteen original scenarios and complete learning layers preserve earlier denominators, exams and frozen histories.

Use academy-measured-cache-lab 0.1.0, Python 3.13+, standard-library runtime. Four unfinished functions/methods separate behavior:
- sample validates exact repeats 1..7 before work/clock access, calls start/work/end per repeat and validates exact nonnegative monotonic integer readings across the run. Return raw durations and the last result reference. Preserve original failures and stop without partial report; effects already completed are not rolled back.
- LruCache.get_or_compute promotes identity hits, counts attempted misses before computation and inserts only successful results. Exact immutable namespace/id/revision keys distinguish caller-defined dependencies. Capacity 1..8 evicts least-recent entries after successful overflow insertion.
- clear releases cache references and resets counters without closing values or revoking borrowers. Reentrant get/clear while computing is rejected before mutation; finally resets the guard after failure. info returns a fixed frozen key/counter snapshot.
- legacy_get warns with caller-located DeprecationWarning before delegating once. It preserves supported generic call/result behavior; warnings-as-errors prevent delegation. This is a stated compatibility exercise, not an invented historical release.

The sampler does not warm up, reset input/cache, change GC, profile or manage global tracing. Repeat/count limits are not elapsed-time/byte budgets. Cached values can be mutable, including None/False/zero; identity is not a deep freeze. Namespace/revision does not enforce authorization or automatic freshness. The custom cache is single-caller, non-reentrant and not thread-safe, a cleanup owner, TTL policy or duplicate-side-effect suppressor.

The guarded demo records environment, workload, variant order, fresh cache state, raw wall/CPU samples, equal results and computation counts. For the stated 32-request/four-key workload, cached computation count is four with 28 hits instead of 32 baseline computations. Timing assertions inspect structure/nonnegative values, never a fixed speedup threshold. Sequential toy ordering and small samples do not establish production percentiles or broad performance claims.

Profile and trace separately from timing. The standalone demo owns fresh tracemalloc state and stops it in finally; runtime imports and library calls do not alter borrowed tracing. Record current/peak/before/fill/clear observations and profile text. Traced allocation is not total RSS/native/deep graph memory; cached/borrowed references determine lifetime.

An authenticated fixed ten-file ZIP excludes maintained solutions/private answer keys. The API serves bytes/stores reported evidence only, never importing or executing learner packages. Trusted maintainer subprocesses verify 61 public cases, examples/types/lint, real source/wheel artifacts and a six-package clean installed typed integration. Prior offload/resource/record/transformation/snapshot contracts remain stable. Supported old/new callers and warning location are tested.

Four manual criteria distinguish comparable measurement, allocation/reference interpretation, cache key/failure/lifetime and installed compatible callers. Actual observations and learner-reported evidence require judgment; finite tests/manual review never award mastery or certify expertise.

## Consequences and next action

This bounded unit is delivered; step 6 and full expert/practical coverage stay open. No academy migration or runtime dependency change is required. CI is configured; remote execution is unobserved. The API continues to use SQLite locally; existing runner PostgreSQL fixtures do not establish academy deployment or service persistence.

Next deliver the first PostgreSQL persistence unit: relational modeling/constraints, parameter binding, transaction ownership and stable identities/duplicate handling with actual PostgreSQL failure/rollback evidence. Then connect FastAPI/SQLAlchemy/Alembic, durable workers/deployment and applied AI. Full operations/comprehensive portfolio/exams remain later steps.

References: [time](https://docs.python.org/3.13/library/time.html), [timeit](https://docs.python.org/3.13/library/timeit.html), [profilers](https://docs.python.org/3.13/library/profile.html), [tracemalloc](https://docs.python.org/3.13/library/tracemalloc.html), [functools](https://docs.python.org/3.13/library/functools.html), [warnings](https://docs.python.org/3.13/library/warnings.html).
