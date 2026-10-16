# Durable outbox lab

A saved record and the intent to publish it must survive together. Implement three functions in src/academy_durable_outbox/core.py: record, consume and publish_one. Keep the supplied types, schema and process fixtures. Initial NotImplementedError failures are expected. The maintained answer is excluded from this download.

## Start with the completed local packages

This extension needs Python 3.13+ and the completed academy-ingestion-service-lab 0.1.0 and academy-competing-ingestion-lab 0.1.0 wheels. These academy distributions are local teaching packages, not published on PyPI. Complete the earlier two starters, run their tests and build their artifacts with python -m build. Follow the earlier README instructions for the PostgreSQL service/migrations and competition evidence. Install both completed wheel files into this lab's fresh virtual environment before installing this project.

From this project directory, create/activate a virtual environment. Install the earlier wheel files with python -m pip install followed by their actual paths, then run:

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
python -m mypy --strict src demo.py crash_worker.py
python -m ruff check src tests demo.py crash_worker.py
python -m build
```

Without ACADEMY_OUTBOX_DSN, database cases explicitly skip. That is not worker/recovery evidence. Configure this private environment variable with generated local PostgreSQL credentials for an explicitly disposable database/schema owner. Never print, commit or reuse the academy's runner token or database. Accepted local DSN fields are host, port, dbname, user, password and options; the earlier adapter rejects unsupported options rather than silently ignoring them. Run all cases and then python demo.py --output observed.json. The demo creates/drops its own schema and prints actual observations, without credentials. The supplied crash_worker.py deliberately terminates its own process at selected boundaries; run it only through the authored fixture in your disposable database.

## Exact contract

Event has namespace, id, revision and value; identity is the complete (namespace,id,revision) tuple. Use prior strict Datum/field rules, including exact integers and zero values. A changed value under the same identity is a conflict, not a new delivery identity. Accepted confirms the same exact validated Event after durable acceptance. Frozen objects are application values, not tamper-proof security boundaries; revalidate boundary values. Never use reading progress, UUID-per-attempt or a cursor as identity/permission.

install is an explicit **one-time** additive schema.sql operation after the prior service_002 migration in an owned disposable schema. It is never called at import or inside requests. It creates delivery_outbox, delivery_inbox and delivery_effect without changing prior package source/contracts. Calling it again raises a database error rather than masking schema drift. The earlier Alembic drift check covers its own service metadata; after these teaching tables are added, it will report extra tables. Production migration/version/drift integration is later work. This is not a live-deployment migration/rollback runbook.

record borrows a PostgreSQL/Psycopg READ COMMITTED Engine. Validate/copy one namespace and at most 64 exact list/tuple Datum values before SQL, preserving order/repeats and rejecting contradictory full keys. Own a fresh Session and one transaction. Provision SourceRow, insert each RecordRow or compare an existing value under a share lock, then insert its stable outbox intent or compare an existing intent. Commit the entire batch before returning Recorded(prior Receipt, enqueued). Count input observations/repeats normally; enqueued counts only new unique event rows. Adopt matching historical records from the unchanged prior API by inserting their missing intent once. A late conflict/error rolls back every new source, record and intent; existing committed facts survive. Repeating an already acknowledged identity never resets acknowledgment. Empty valid input returns zero without opening a connection. Do not call the earlier ingest inside this transaction: it owns/commits its own transaction and cannot make the outbox atomic with a later write.

consume validates/copies one exact Event, owns a fresh Session/transaction, inserts its complete key/value into delivery_inbox and increments delivery_effect(total,applied) only for a new inbox key. Same-value repeats confirm acceptance without applying again; different values raise ConflictingEvent. Inbox and aggregate commit together. A real database failure rolls both back. Return Accepted only after commit. Scope arguments require the caller's prior application authorization. This sink models one durable database effect; it does not make payments, email or arbitrary external effects idempotent.

publish_one validates namespace/callable, owns one fresh Session/transaction and selects one pending row ordered by id/revision FOR UPDATE SKIP LOCKED. Hold that row lock while invoking the borrowed trusted publisher exactly once. A successful callback must return exact Accepted for the unchanged persisted Event **after** its durable acceptance. Validate confirmation/identity, update acknowledged=true, commit, then return the Event. Return None if no row was available in that statement; another worker may still hold pending rows. A failure, invalid acknowledgment, lost response or process death keeps the event pending. The publisher may already have committed; producer rollback cannot undo that effect. No automatic in-call retry or catch-all suppression is permitted. Different workers may deliver later keys first; this is not global ordering/fairness.

Use the prior owned_session helper with RetryPolicy(max_attempts=1, delays=()) for transaction-local 2000ms lock/5000ms statement limits. These do not interrupt a blocked publisher or impose a hard total deadline. Every function owns its Session; the Engine and callback remain borrowed. The two-connection pool suffices for one worker plus the supplied independently committed consumer. Competing fixtures use one pool per worker so held claims cannot exhaust the consumer pool. Do not call the consumer with the producer Session or share a Session across threads.

## Required evidence

Run the public suite against actual disposable PostgreSQL. Capture the real 23514 consumer rollback, foreign-key rejection, late batch rollback, prior-fact adoption, scoped reads, duplicate identities/revisions/zero values, SKIP LOCKED unavailable-versus-empty behavior and separate worker ownership. Show setting reset and zero checked-out connections after failures.

The three subprocess fixtures prove:

1. Exit 71 before producer commit: neither source fact nor intent becomes committed. Re-record, then deliver normally.
2. Exit 72 after producer commit: one fact and pending intent survive worker death; a restarted worker delivers it.
3. Exit 73 after consumer commit before producer acknowledgment: one applied effect survives and the intent remains pending. Restart delivers the same identity again; inbox deduplication preserves exactly one database application before acknowledgment commits.

The parent observes pg_stat_activity until the terminated child's connections disappear, then inspects database state/restarts. Sleep only paces observation. The process really exits without context-manager cleanup; PostgreSQL stays running. The disposable helper database uses tmpfs, so this does **not** prove database restart, power-loss, backup/restore or full production durability. A separately labeled modeled lost-response test is not a real network incident. The sink is PostgreSQL, not a real broker. Publisher return values are a trusted protocol contract, not independently verified remote receipts.

## Review checklist and next work

Provide actual pytest/type/lint/build/fresh-install output and observed.json. Add two regressions, explain claim/publish/ack and inbox/effect boundaries, and ask a reviewer to inspect the implementation and limits. Four academy criteria separate atomic identity, worker confirmation, consumer replay and installed evidence. Reported tests/checklists/manual reviews never award mastery.

The unchanged previous HTTP API still authenticates/authorizes and returns only id/revision/value. Its POST route does not call record or enqueue automatically; adopt through record explicitly. Real broker adapters, delivery schemas/versioning, leases/fencing, bounded admission/backoff, poison-message policy, graceful shutdown, retention and operational migrations are later units. No exactly-once transport, production load, distributed permission or hostile-code sandbox claim is made.
