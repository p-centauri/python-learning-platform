# Ingestion service lab

Build a bounded permission-scoped ingestion API on FastAPI, Pydantic, SQLAlchemy and Alembic. Implement authorize in auth.py, plus ingest and read_page in service.py. Routing, strict models, ORM metadata, migrations, local demo/server and public tests are supplied. The academy serves this authored starter and stores manual evidence; it never executes learner packages.

## Run locally

Use Python 3.13+ and an **explicitly disposable PostgreSQL 17 database** that permits creating/dropping schemas. The public fixture/demo create unique schemas and remove only those schemas. Never use the academy/production database. Credentials belong in local environment configuration, not code, screenshots or submitted output.

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e '.[dev]'
    export ACADEMY_SERVICE_DSN='host=127.0.0.1 port=5432 dbname=disposable user=lab password=YOUR_LOCAL_PASSWORD'
    python -m pytest -q
    python -m mypy --strict src demo.py serve.py
    python -m ruff check src demo.py serve.py tests
    python demo.py --output service.json
    python -m build

Without ACADEMY_SERVICE_DSN database cases explicitly skip; an offline green run does not evaluate PostgreSQL. Maintainers run make verify-ingestion-service against their owned pinned disposable container, not learner uploads. The API demo uses HTTPX in-process ASGI and real PostgreSQL; it does not test DNS/TLS/proxies. The installed verifier separately checks the supplied loopback TCP server.

## HTTP contract

POST /namespaces/{namespace}/readings accepts application/json with only items (0..64 objects). Each object has only id, revision and value. Exact ASCII id [a-z][a-z0-9-]{0,31}, exact integer revision 1..8 and value 0..1000000; strings/floats/bools do not become integers. Zero is valid. HTTP 200 returns observed/inserted/duplicates only, after commit. This bulk operation intentionally uses 200 for both initial and repeated successful batches; it makes no single-resource Location promise. Changed value under the same namespace/id/revision causes 409 and whole-batch rollback.

GET the same path accepts limit as canonical decimal string 1..32 (default 16), and paired after_id/after_revision (revision 1..8). It returns only items with id/revision/value and optional next_cursor with id/revision. Fixed C-collated id/revision order and limit+1 observation establish more data. No total count/complete snapshot/pagination across arbitrary mutation is promised. The cursor is an unsigned position, not an authorization grant; every page still filters the authorized namespace.

Missing/invalid bearer is 401 with WWW-Authenticate: Bearer; a known credential for another namespace is 403; invalid JSON/body/query is 422 with generic detail, not echoed input. A changed fact is 409. DBAPI errors and bounded pool exhaustion are private 503 storage operation failed, without SQL, DSN, raw rows or automatic retry instructions. A 503 does not prove nothing committed; reconcile stable keys after an uncertain commit. Unsupported methods remain 405. GET /health is liveness only; GET /ready checks the expected Alembic head and returns 503 for missing/old schema. Request responses carry generated X-Request-ID and Cache-Control: no-store; the fixed request_completed log has trace/status only. Unexpected process failures are not a guarantee of a logged/formed response.

## Permission function

create_app borrows an explicitly configured PostgreSQL Engine and snapshots 1..8 credential-to-single-namespace entries. Tokens are caller-generated ASCII [A-Za-z0-9_-]{16,64}; no built-in credential exists. authorize receives this trusted mapping, an optional Authorization header and path namespace. Reject missing/wrong scheme/malformed/unknown tokens with AuthenticationRequired. Bearer scheme is case-insensitive, separator is one space; no token whitespace. Use hmac.compare_digest on configured tokens, never token values in messages/logs. Authenticate before namespace validation. Validate the namespace, then exact-match the authenticated scope; another namespace raises PermissionDenied. Return the authorized namespace.

Permission is checked before the database session dependency. Body-provided namespace is forbidden. The lab's configured credentials are a local teaching mechanism, not account management/OAuth, a password-recovery system or public-deployment readiness. Use the academy's separate real accounts for learning evidence; never reuse those sessions/tokens here.

## Session and transaction functions

The app dependency owns one Session per request and closes it at function scope, returning pooled connections before sending a handled response. It never commits in late cleanup. Caller owns Engine disposal and migrations. Synchronous route functions use synchronous database I/O; putting blocking ORM work in async def does not make it asynchronous. A Session tracks objects and starts transactions lazily; it is not a connection, and sharing one Session between requests/tasks is unsupported.

ingest validates namespace, exact built-in list/tuple length 0..64 and exact revalidated Datum objects before SQL. Borrow the idle Session; reject session.in_transaction() without committing, rolling back or closing caller work. Own one session.begin() block. If nonempty, INSERT SourceRow with ON CONFLICT DO NOTHING. For each Datum, INSERT RecordRow with the complete conflict key and RETURNING value. A returned value including 0 counts as inserted. Otherwise select existing value by the full key FOR SHARE: same value counts duplicate; missing/different raises ConflictingDatum. No overwrite, SELECT-before-INSERT absence assumption or extra commits. Return Receipt only after successful commit, with observed=inserted+duplicates. Errors leave healthy sessions idle through rollback, preserving earlier committed rows and native exception/cause. No partial success result.

read_page validates namespace, exact int limit 1..32 and optional exact/revalidated Cursor, then requires an idle Session. Own one read transaction. Filter namespace always; if a cursor exists, filter id>after.id OR(id=after.id AND revision>after.revision). The columns have C collation. Order id/revision, observe limit+1. Materialize immutable Datum values while the session transaction is active, return at most limit items, next_cursor equal to the last returned key only when one extra was observed. Never return an ORM object or include ingested_at/namespace/credentials. Reads do not provision a source. Query predicates use SQLAlchemy bound expressions, not textual caller interpolation.

Counts limit accepted/returned items, not request bytes before JSON parsing, blocked iterators, total query work/storage or an operation deadline. This is a dedicated append-only READ COMMITTED protocol with no concurrent Session use, external UPDATE/DELETE/TRUNCATE/DDL or hostile schema replacement. Keyset pages over changing data are not a frozen dataset: a backfill behind the cursor may not appear. Competing transactions/retries/locks/index measurements and worker recovery are separate later units.

## Migrations and server

Migration service_001 creates source/reading constraints. service_002 adds required server-default timezone-aware ingested_at without altering key/value rows. Supplied upgrade/downgrade/check_migrations use explicit caller-owned engine/connection scopes and packaged migration files. ORM metadata does not install schema; the app never calls create_all or runs migrations on each request. Readiness checks head, not full drift; check_migrations separately compares metadata.

Downgrade to service_001 intentionally loses ingested_at metadata while retaining original key/value rows; re-upgrade assigns new timestamps. Downgrade to base destroys these lab tables and is rehearsed only in disposable schemas. This is not a production zero-downtime migration/backup/restore proof. Review generated proposals rather than apply them blindly.

For manual HTTP requests, first provision a disposable schema and apply upgrade(engine) to it in a local setup script; retain its DSN options search_path. Configure ACADEMY_SERVICE_TOKENS as private JSON mapping generated credentials to namespaces, then run `python serve.py --port 8010`. The supplied server binds 127.0.0.1 only, never migrates automatically and disposes its owned engine on shutdown. /ready must pass before data requests. Tokens must remain private; the maintainer's TCP check generates its own credentials rather than require a shared default.

## Review evidence

1. Show strict payloads, output allowlists and explicit HTTP statuses. Explain method semantics, no-store and body/byte/timeout limits.
2. Show auth 401 versus permission 403, rejected credential/body/cursor attempts before SQL, namespace filters and fixed safe request logs. Explain local credentials versus public authentication.
3. Show actual PostgreSQL first/repeated counts, late 409/503 rollback, separate observer visibility, commit-boundary fault injection, idle caller preservation and zero checked-out pooled connections. Distinguish a modeled pre-commit failure from an uncertain real network commit.
4. Record migration upgrade/downgrade/re-upgrade with key/value preservation and explicit timestamp loss, metadata check, readiness gates, actual JSON, tests/types/lint/source/wheel/fresh-install and a typed prior Record/Row/Reading adapter. Add two meaningful regressions and explain keyset data-change limits.

Public finite tests, reading/checklists and learner-reported output do not award mastery or certify expertise. The app pins four manual criteria and preserves submissions/reviews; it does not independently verify your local output. Keep worker recovery, distributed retry, TLS/proxies, public hosting and full academy deployment as later work.

The local DSN adapter supports explicit host/dbname/user, optional port/password and trusted options (search_path). Other options, including SSL requirements, are rejected rather than silently dropped; TLS/provider deployment is a separate unit.
