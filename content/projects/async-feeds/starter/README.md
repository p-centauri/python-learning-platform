# Bounded async feed-ingestion lab

Build a small multi-source ingestion job with explicit work limits and cleanup. Run it locally on trusted code and configured destinations. The academy serves this starter and stores your reported evidence; it never executes this package or grades uploaded projects. Passing public checks is separate from mastery and manual review.

## Setup and tools

Use Python 3.13 or later in a fresh virtual environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
python -m mypy src/academy_async_feeds demo.py
python -m ruff check src tests demo.py
python demo.py
python -m build
```

The unfinished starter fails. Implement `iter_records`, `open_feed` and `ingest`; the maintained reference is excluded from the download. The demo uses HTTPX MockTransport, never a live server. Expected stdout is `{"count": 4, "sources": 2, "total": 30}` and stderr is empty. Importing the package must not create tasks, clients or event loops, configure logging, or perform network calls. HTTPX 0.28.1 is the runtime dependency; pytest 9.0.3, mypy, Ruff and build are development tools. Tests use `asyncio.run` with an outer watchdog, so no pytest-asyncio plugin is required. Dependency setup needs the configured package index unless an offline wheelhouse is supplied.

## Parsing contract

`iter_records(chunks)` is a lazy async generator over borrowed byte chunks. Do not close its input or materialize all chunks/records. Chunks may split anywhere or contain several records; empty chunks do nothing. LF separates physical lines; final nonempty bytes form an EOF record. JSON whitespace, including CR before LF, is accepted, but blank physical lines are invalid. A trailing LF does not add a blank record. Empty input returns no records.

Each line contains at most 1024 bytes excluding LF, including whitespace and a CR if present. The limit is inclusive; reject an oversized pending line before extending the buffer beyond the bound. Decode strict UTF-8 and parse JSON. Require exactly `id` and `value`: ID matches `[a-z][a-z0-9-]{0,31}` and value is an actual integer (not bool) from 0 through 60000 inclusive. Return frozen `Record` values. Reject non-byte chunks. `RecordError` names the one-based physical line without echoing input; UTF-8/JSON failures preserve their original cause. These causes may contain rejected data, so do not publish them as safe logs.

## HTTP ownership contract

`open_feed(source, *, client, max_bytes=8192)` is an async context manager. Validate Source and the byte limit before requesting. Source label is 1–32 lowercase ASCII letters/digits/hyphens beginning with a letter. URL is at most 2048 characters, HTTPS with a hostname, no username/password, fragment, whitespace/control characters or nonstandard port. This is syntax validation, **not SSRF protection**. Only use destinations selected by trusted application configuration; the academy does not offer this as a URL-fetch endpoint.

Borrow the supplied AsyncClient; never close it. Own and close the response, raw chunk generator and parser on exhaustion, early exit, parsing failure, caller failure and cooperative cancellation. Request GET with redirects disabled even when the client defaults to following them. Accept status 200, `application/x-ndjson` with optional parameters, and absent/identity Content-Encoding. Reject compression and other status/media types. Count actual emitted raw-body bytes with an inclusive 1–8192 limit; ignore Content-Length for enforcement. Read raw chunks in bounded 256-byte pieces. This limits parser pending bytes and processed raw bytes; it does not prove a hard bound on HTTPX, socket or transport buffering.

Wrap HTTP acquisition/read failures in FeedError with the HTTP error class only and the original cause. Do not wrap a caller's own exception merely because it is an HTTPX exception. No retries or direct printing/logging. Client-level HTTP timeouts remain operation-specific; the job adds an overall cooperative deadline.

## Worker contract

`ingest(sources, *, opener, workers=2, queue_size=2, timeout=1.0)` accepts a finite Sequence of zero through 16 Source objects; reject strings/bytes and invalid elements. Validate all sources/options and duplicate labels before starting I/O, then snapshot the sequence so later caller mutation does not change the job. Worker count is an actual int in 1–4; queue size is an actual int in 1–16. Timeout is a finite int/float in (0, 30], excluding bool. Invalid settings raise ConfigError. A valid empty job returns zero counts and opens nothing.

For nonempty input create exactly the configured worker tasks plus one producer inside a TaskGroup, and use an asyncio.Queue with the configured positive maxsize. Wait for capacity when adding work. Never create one task per source or hold all records in a list. Workers consume one source at a time through the injected async context manager, total records in one pass, and balance every successful get with task_done, including stop sentinels and failures. The producer sends one None sentinel per worker after enqueueing all sources. The queue is ephemeral; task_done is local accounting, not durable acknowledgment.

Return `{"sources": N, "count": C, "total": T}` only after every source has fully consumed and its owner has closed successfully, and all tasks have finished. Count all records even if IDs repeat; this lab provides no database deduplication. Keep only up to 16 per-source aggregates, not records. Results are fresh per invocation. There is no returned partial success, persistence, automatic retry or success side effect; this is not a database transaction or rollback system.

An ordinary worker/open/cleanup failure leaves the TaskGroup as an ExceptionGroup containing the original uncaught failure(s), after related tasks are cancelled and awaited. Preserve this structure rather than flattening it. Caller cancellation must propagate CancelledError after cooperative owned cleanup. A total job deadline includes opening, queue waits, reads and TaskGroup exit; it becomes TimeoutError outside asyncio.timeout. Cancellation is a request at an await boundary, not a hard execution/cleanup limit. Blocking code, suppressed cancellation or uncooperative cleanup can overrun it and are outside this trusted lab contract.

TaskGroup treats a child's CancelledError differently from an ordinary failure. Verify every source completed before returning; a child-only cancellation must never produce a partial report. It may surface as incomplete FeedError after group exit, or as the job TimeoutError if abandoned work blocks the producer. Tests use controlled cooperative openers. KeyboardInterrupt/SystemExit keep their special TaskGroup behavior.

## Evidence for review

Run all 75 public pytest cases and show collection/output/tool versions. The cases cover framing, ownership, bounded workers/queue, failure groups, cancellation, deadline, cleanup failure, fresh totals and configuration snapshots. They use Events for ordering and a watchdog for deadlocks, without asserting exact elapsed performance. Add two regressions: one failure after a valid record and one cancellation while waiting for a source. Explain the observable outcome and what your doubles bypass.

Build wheel/source archive, install your wheel into another environment, then run tests and the demo outside the checkout. Connect the prior policy lab through a typed filtering opener: own the HTTP stream, borrow its records, apply the existing selector and close your filtering generator. Keep previous packages unchanged. Submit a repository/artifact link, reported test results, ownership/work-limit reasoning and known gaps for the four manual rubric criteria. Finite tests and self/human reviews do not certify Python expertise or production service readiness. Persistence, retries/recovery, hostile execution and full backend/AI paths remain later work.
