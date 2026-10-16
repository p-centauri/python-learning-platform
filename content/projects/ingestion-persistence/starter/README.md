# Ingestion persistence lab

Store bounded validated readings in PostgreSQL without losing transaction ownership or confusing a duplicate with a changed value. Implement the three unfinished functions in store.py. The schema, value objects and tests are supplied. Tests are public finite checks, not an expert certificate. The app saves reported evidence and manual reviews; it never runs this package.

## Local setup

Use Python 3.13+ and a **disposable PostgreSQL 17 database** that permits creating/dropping schemas. Never point these tests or demo at the academy database or production data. They create uniquely named schemas and remove only those schemas. Keep the connection string in an environment variable; do not submit passwords or print the DSN.

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e '.[dev]'
    export ACADEMY_PERSISTENCE_DSN='host=127.0.0.1 port=5432 dbname=disposable user=lab password=YOUR_LOCAL_PASSWORD'
    python -m pytest -q
    python -m mypy --strict src demo.py
    python -m ruff check src demo.py tests
    python demo.py --output persistence.json

Without that variable PostgreSQL cases explicitly **skip**, so an offline green result does not evaluate persistence. All cases require a running disposable server for complete evidence. Maintainers use the repo's make verify-ingestion-persistence with an owned digest-pinned disposable container. Learners may run their own local PostgreSQL. Driver psycopg2-binary 2.9.10 matches the academy's current driver; this teaching pin is not a recommendation for all production deployments. types-psycopg2 supplies checker stubs, not runtime behavior.

## Exact contracts

Reading is supplied and frozen: exact built-in namespace/id strings match ASCII [a-z][a-z0-9-]{0,31}; revision is an exact int 1..8; value is an exact int 0..1000000. Booleans/floats are rejected. The key is (namespace, id, revision); value is immutable under this key. Namespace is an application discriminator, not authorization. Revision is chosen by the caller, not an automatic current-version policy.

snapshot_batch borrows one Iterable[Reading], preserves references and order (including duplicates), accepts 0..64 exact Readings and revalidates fields. The 65th observation proves overflow and raises ValueError; observe no 66th item. Wrong row types also raise ValueError. Original iterator errors propagate. Never close borrowed input. Counts bound observations, not blocked iterator time or deep memory. Input side effects are not rolled back.

persist_batch snapshots/validates the whole input **before database access**, then requires an open, idle, non-autocommit connection explicitly configured to READ COMMITTED. Caller configures trusted search_path to the supplied schema and owns connection closure. Reject other states with ValueError without commit/rollback/close or configuration changes. The library owns a new transaction and cursor only; do not nest inside caller work. Even an empty batch returns BatchResult(0,0,0) with an idle reusable connection.

Within one transaction, provision each namespace using INSERT ... ON CONFLICT (namespace) DO NOTHING. Insert each reading with four separately bound values and ON CONFLICT (namespace,id,revision) DO NOTHING RETURNING value. A returned row counts as inserted. Otherwise SELECT the same full key FOR SHARE and compare stored value: exact same value counts as a duplicate; missing/different value raises ConflictingReading. Never blindly overwrite. Within-batch repeats count too. No application preflight SELECT-before-INSERT race or rowcount guessing is needed.

Return frozen BatchResult(observed,inserted,duplicates) **only after commit**; observed=inserted+duplicates. A conflict or driver exception rolls back the entire batch, including newly provisioned namespaces, preserving earlier committed rows and leaving an ordinary healthy connection idle/open. Original driver exception types/SQLSTATE remain available. Rollback itself can fail if a connection breaks; preserve the native exception chain. Lost commit acknowledgment can leave an unknown outcome: reconnect/reconcile stable keys rather than promise exactly-once delivery. No automatic retries, external effects or durable worker acknowledgments occur.

load_namespace validates the namespace before DB access, uses the same idle/READ COMMITTED/borrowed owner rules and owns one read transaction. Select separately bound namespace, order by id COLLATE "C" then revision, LIMIT 65. Return a tuple of Readings for 0..64 rows; 65 means ValueError with rollback, no partial result. Reads neither provision a namespace nor change data. This limit does not bound all rows stored across repeated batches, query latency or database storage.

## Database contracts and scope

schema.sql supplies NOT NULL, primary/composite keys, foreign key and named CHECK constraints. Python validates convenient input; the database also rejects invalid direct SQL. A CHECK alone accepts NULL when its expression is unknown, so keep NOT NULL. Setup owns DDL separately: request functions never install/drop the schema. This file is a teaching baseline, not a migration framework; SQLAlchemy/Alembic integration follows later.

The protocol is append-only, using dedicated READ COMMITTED connections with no concurrent use of one connection, external UPDATE/DELETE/TRUNCATE/DDL or hostile search_path/schema replacement. PostgreSQL constraints arbitrate writes; the bounded test suite does not prove the academy's multi-instance concurrency/backup/deployment operations. Connection/statement/lock timeouts are different controls; counts are not a total deadline. Callers can configure local statement/lock limits for their disposable server. No live HTTP source, retries, cache invalidation, authentication/RLS or distributed exactly-once claim belongs to this unit.

## Evidence for manual review

1. Model the two tables and explain NOT NULL, CHECK, key and foreign-key failures. Record actual server/driver version and SQLSTATE from direct SQL.
2. Show actual first/repeated batch counts, full key distinctions, second-connection visibility and a late conflict that rolls back new rows/namespaces while retaining earlier data. Explain input effects versus database rollback and unknown commit outcomes.
3. Record safe parameter binding, idle/active/failed/closed/autocommit/isolation behavior, deterministic ordered/bounded reads and borrowed connection/input ownership. Add two meaningful failure regressions.
4. Build source archive then wheel, install outside source, run tests/types/demo there and adapt earlier installed Record/Row values into Readings without changing those earlier libraries. Preserve actual command output and persistence.json. Do not substitute invented output for evidence.

    python -m build

A wheel from the unfinished starter still contains unfinished functions. Run your built artifact in a fresh environment with driver, pytest/mypy/stubs installed, no PYTHONPATH/MYPYPATH, and tests/demo copied outside source. Reading, checklist completion and manual judgments remain separate from objective grading and mastery.
