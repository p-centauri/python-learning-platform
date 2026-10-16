# Competing ingestion lab

Extend the **completed prior ingestion-service package** with bounded transaction retry and read-only reconciliation. Implement classify_sqlstate and retry_ingest in retry.py, plus reconcile in reconcile.py. The supplied contracts/session helper, experiments and tests reuse the earlier service without changing it. The academy serves authored bytes and stores manual evidence; it never executes these packages.

## Setup and run

Use Python 3.13+ and a separate **explicitly disposable PostgreSQL 17 database** that allows creating/dropping schemas. The fixture/demo own unique schemas and clean only their own schema. Never use the academy or production database. For the controlled deadlock experiment, server deadlock_timeout must be below 2000 milliseconds (the PostgreSQL default is 1000); the experiment checks this and fails clearly otherwise. No superuser-only setting is changed by the package.

First download and finish the prior [ingestion service lab](/api/projects/python-ingestion-service/starter), run its checks and build its wheel. These local academy packages are not published on PyPI. Install the completed prior wheel before this extension:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install /absolute/path/to/academy_ingestion_service_lab-0.1.0-py3-none-any.whl
    python -m pip install -e '.[dev]'
    export ACADEMY_COMPETITION_DSN='host=127.0.0.1 port=5432 dbname=disposable user=lab password=YOUR_LOCAL_PASSWORD'
    python -m pytest -q
    python -m mypy --strict src demo.py
    python -m ruff check src demo.py tests
    python demo.py --output competition.json
    python -m build

Keep credentials/DSNs in private local environment configuration, never source, screenshots or submitted output. The DSN adapter is the previous local-only explicit host/dbname/user adapter; unsupported TLS/provider options are rejected, not silently dropped. Missing ACADEMY_COMPETITION_DSN labels database cases as skipped. Skips are not concurrency evaluation. Maintainers run make verify-competing-ingestion with trusted references on their own disposable container, never learner uploads.

## classify_sqlstate

Accept an exact built-in five-character uppercase ASCII [0-9A-Z] SQLSTATE or None; malformed/wrong-type inputs raise ValueError. Never classify by driver message words. Return Decision.RETRY for 40001/40P01; Decision.RECONCILE for None, any class 08 code, 57P01 or 57P02; Decision.STOP for every other valid code. This is this lab's conservative policy, not a universal database rule. In particular 55P03 lock timeout, 57014 statement cancellation and 23505/23514 constraints stop here. Domain/programming/pool/sleeper failures are not DBAPI retry cases.

## retry_ingest

Accept the explicit caller-owned PostgreSQL/Psycopg Engine, one validated namespace and an exact list/tuple of at most 64 exact revalidated prior Datum values. Copy their fields into new frozen values once before SQL so later caller mutations cannot alter retries. Preserve order/repeats; different values for one complete id/revision key raise ConflictingDatum before SQL. Namespace is a trusted scope after the caller's authorization, not an access grant.

Use the supplied require_engine, RetryPolicy validation and owned_session helpers. Each attempt owns a fresh Session; the existing ingest owns its transaction, duplicate/conflict logic and commit-before-receipt. The after_begin Connection hook checks READ COMMITTED and binds transaction-local lock/statement settings without starting a caller Session transaction early. The Engine remains borrowed and is never disposed or globally reconfigured.

Catch only DBAPIError after the Session context has finished rollback/closure. Get orig.pgcode, classify it, and either return Delivery(receipt, actual_attempts), retry the full transaction, raise fixed UnknownOutcome(actual_attempts) from the original for reconciliation, or re-raise the original stop failure. At the final permitted failure raise RetryExhausted(attempts, sqlstate) from the original. Never include failed-attempt counts in the final Receipt. Invoke the borrowed sleeper with the corresponding policy delay only between permitted attempts after cleanup; original sleeper errors stop immediately. Do not print native causes containing SQL/credentials.

RetryPolicy permits exact attempt integers 1..3, exact lock limits 50..2000 ms, a larger exact statement limit at most 5000 ms, and one exact finite float delay 0..1 seconds per possible retry. Defaults are three attempts, 2000/5000 ms and two zero delays for reproducible fixtures. A caller can supply an explicit bounded jitter schedule; the policy does not claim fairness or production backoff. A server lock acquisition or statement limit is not a hard whole-operation deadline or a pool/input/remote-effect limit.

## reconcile

Validate/copy the same bounded facts before SQL; reject a contradictory batch. Own a fresh READ COMMITTED Session/read transaction using the supplied local-limit helper. Select only the requested complete id/revision keys under the namespace with bound SQLAlchemy expressions. Build Reconciliation(matched_keys, missing, conflicts): counts use unique keys, missing/conflicts contain expected Datum values in first-key appearance order, and matching zero is valid. Conflict has priority, then missing, otherwise complete. Empty input is complete with zero counts and no SQL. Never provision sources, mutate rows or expose ORM/internal timestamp fields.

Complete means all requested key/value facts were observed, not that a particular previous transaction committed. Another writer may have stored identical values; original inserted/duplicate counts cannot be reconstructed. Missing is absence in one statement view, not rollback proof: a pending writer may commit afterward. No state automatically grants permission to replay. Existing API permissions remain in the earlier service; this library adds no endpoint or authentication flow.

## Observed experiments and modeled faults

The supplied experiments run only in the disposable migrated schema. Separate threads own separate Sessions and are joined; a separate driver observer verifies pg_blocking_pids before releasing a holder. Finite events/barriers/polling organize a fixture, never fabricate a database result. Four races verify same/different values after holder commit/rollback. Snapshot experiments establish real READ COMMITTED versus REPEATABLE READ views. A separate SERIALIZABLE gate shows actual 40001 and fresh decision reevaluation; it does not change the delivery wrapper's READ COMMITTED contract.

Two inverse-order writers produce real 40P01; the victim is unspecified, rolls back and uses a fresh complete attempt. The experiment-specific barrier must not be reused for writers blocked before reaching it. Consistent full-key order among all cooperating writers can prevent this particular cycle; it does not prove arbitrary deadlock freedom. A held-lock experiment observes 55P03; a slow statement observes 57014, with local reset/pool cleanup.

The modeled acknowledgment-loss case commits real data and then injects a DBAPI failure. It verifies one stopped attempt and read-only complete reconciliation, **not a real broken-network commit incident**. Another actual case observes missing during an uncommitted write and complete after commit. The demo saves actual server/package versions, observations, attempts/final facts, API permission responses and checked-out counts. It uses HTTPX ASGI for the previous API, not DNS/TLS/proxies or a load benchmark.

## Manual evidence

1. Record actual visibility counts, observed blocker edges, commit/rollback/race outcomes, 40001/40P01/55P03/57014 and joined cleanup. Explain isolation/lock/statement/total-time differences.
2. Show copied stable input, fresh attempt Sessions, cleanup before delay, final committed counts and finite stop/exhaustion/native causes. Explain what is replay-safe and what is not.
3. Show namespace/full keys/values, zero/repeated keys, conflict/missing/complete, in-flight absence and modeled loss. Separate observed state from transaction attribution or replay permission; preserve application authorization.
4. Build both wheels from source archives, install freshly outside source, run copied tests/demo without PYTHONPATH/MYPYPATH, save actual JSON/output and add two regressions with stated limits.

The four criteria are pinned manual review. Public tests, reading/checklists, reported output and self/human judgment do not award mastery or certify expertise. Finite two-writer evidence does not establish production fairness/stress, durable acknowledgments, exactly-once delivery, crash recovery or full academy deployment. Workers/outbox/recovery, broader PostgreSQL/API depth and applied AI are later units.
