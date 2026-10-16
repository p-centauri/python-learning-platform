# ADR 0018: bounded async feed ingestion and cooperative shutdown

Date: 2026-10-03. Status: accepted.

## Context

Step 6 now has packaged synchronous ingestion and a separate function/testing policy extension. The next unit needs observable async ownership, work limits and failure behavior, without silently changing those published contracts or running learner packages inside the API.

## Decision

Publish eight ordered lessons and the separate `academy-async-feeds-lab` v0.1.0. Runtime depends on HTTPX 0.28.1 and Python 3.13+. Three unfinished functions cover lazy strict async NDJSON parsing, a managed asynchronous HTTP adapter, and a bounded multi-source job. Configuration is validated and snapshotted before I/O. Cap sources at 16, workers at 4, queue capacity at 16, line bytes at 1024 and processed body bytes at 8192 per source. A fixed worker pool plus one producer bounds created work; a positive queue capacity provides backpressure. Queue accounting is local and ephemeral.

The application owns a reusable AsyncClient. The HTTP helper owns its response, raw chunk generator and parser; it closes them on exhaustion, early exit, ordinary failure and cooperative cancellation. Catch HTTP acquisition/read errors at their own boundaries, preserving causes and caller exception identity. Source syntax validation is not destination authorization or SSRF protection. Raw response policy matches the earlier synchronous lab, but the implementation and version are separate.

TaskGroup owns related tasks and preserves uncaught grouped failures after cancellation/awaited cleanup. Return one aggregate only when every source completes and closes successfully. Check completeness explicitly because child CancelledError is special. Caller cancellation propagates, and an overall asyncio timeout covers queue waits, opening, reads and group exit. This budget is cooperative: blocking or cancellation-suppressing code and uncooperative cleanup can overrun it. No database writes, retries, external success publication, rollback or durable-worker guarantees are added.

The 75 public cases use pytest with standard-library event loops; no async test plugin is required. Events establish preconditions, observable streams/queues show behavior, and outer watchdogs detect test deadlocks without claiming exact elapsed performance. Include awaited async cleanup, late/cleanup failures, borrowed client reuse, child-only incomplete outcomes, fresh aggregates and configuration snapshots. Build/install trusted references in temporary maintainer environments and strictly type-check composition with the prior selector through an async opener. No learner uploads execute in these checks.

Catalog `2026.10-async-v1` uses a new `Python async ingestion` skill, preserving earlier question sets and denominators. New interactive/recall content advances to v4; rubric content is `2026.10-project-review-v4`. Submitted evidence retains its snapshots. The authenticated starter is an eleven-file allowlist excluding references/private keys. Four manual review criteria assess supplied evidence; reading, guided work, checklists and reported test output do not award mastery.

## Consequences and limits

This completes the bounded async unit, not step 6 or Python expertise. Advanced object/typing/concurrency/measurement units, PostgreSQL/FastAPI persistence, workers/recovery and applied AI paths remain open. MockTransport does not prove DNS/TLS behavior, destination trust, socket allocation limits or production operation. Remote CI is configured but requires its own observed evidence.

References: [coroutines and tasks](https://docs.python.org/3.13/library/asyncio-task.html), [queues](https://docs.python.org/3.13/library/asyncio-queue.html), [Event](https://docs.python.org/3.13/library/asyncio-sync.html#event), [contextlib](https://docs.python.org/3.13/library/contextlib.html), [HTTPX async ownership](https://www.python-httpx.org/async/).
