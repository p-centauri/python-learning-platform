# Leased outbox worker lab

Complete the previous service, competition and outbox packages first. Their local wheels are dependencies, not PyPI packages. This extension keeps the prior Event/Accepted/record/consume contracts and HTTP routes unchanged.

Implement three functions in src/academy_leased_worker/core.py: claim, settle and run. Shared values, SQL resources and owned fixture helpers are supplied. The academy serves authored files and stores reported evidence; it never executes your package.

## Exact contract

- Borrow a PostgreSQL/Psycopg Engine configured by the prior service. Use fresh owned Sessions with READ COMMITTED, transaction-local 2000ms lock and 5000ms statement limits. Commit or roll back before returning. Never dispose the borrowed engine.
- Record the namespace's facts/intents before claiming. Persist the first exact Policy (lease 100..60000ms, attempts 1..8, one tuple integer delay 0..60000ms per retry). A later differing policy must fail without changing jobs. Scope permission remains the caller's responsibility.
- In one short claim transaction adopt at most 64 unacknowledged intents and quarantine at most 64 expired final-attempt leases. Claim one eligible job in C id/revision order with FOR UPDATE SKIP LOCKED. Already acknowledged facts are not adopted. None means no lease returned in this statement, not globally empty or fairly scheduled.
- Initial ready jobs use next_at. A retry after explicit failure uses settlement database clock + the delay for that completed attempt. An expired lease becomes eligible at saved lease_until + that same delay. Each committed claim consumes an attempt, even if the process never publishes. A final expired claim is quarantined. Use clock_timestamp(), not a transaction-start clock or a worker laptop clock.
- Increment the job generation on each claim and return a frozen copied Event/generation/aware deadline after commit. Release the connection before calling publication. Event identity stays namespace/id/revision; attempts never change it.
- settle accepts only an exact Accepted with the complete leased event or Failure.RETRY/POISON. Guard the current job state, generation, exact saved deadline and a live deadline checked by PostgreSQL at the write. Check the persisted value too. Invalid confirmation raises ValueError; a stale or mismatched job returns False and changes nothing. Tokens fence this database writer; they are not credentials or protection against a malicious caller.
- Accepted moves the job to done and acknowledges its outbox row in one transaction. A retry moves it to ready at the saved future time, or to dead/exhausted at the attempt limit. Poison moves it to dead/poison immediately. Quarantine retains the unacknowledged intent; recording the same fact does not silently redrive it. Repair/redrive/retention tools are future work.
- run admits one callback at a time, at most limit exact-int 1..64 claims (default 8), and checks an exact threading.Event before each claim. It returns Report(attempted,settled,stale); settled includes durable retry/poison decisions, not only acceptance. A stop observed while a callback runs prevents the next claim; it does not undo the admitted attempt.
- The callback receives a separate Event copy. Reject mutation or false confirmation. An ordinary callback/validation exception attempts to schedule Failure.RETRY, then re-raises the original exception. If that scheduling also fails, expiry is the recovery path. BaseException and abrupt process death leave the lease to expire. Do not retry failed SQL automatically.

## Local verification

Use an owned disposable PostgreSQL 17 database. Never point these schema/test helpers at shared or valuable data. Explicit setup is prior upgrade(engine), prior outbox install(engine), then this install(engine); the additive SQL is one-time teaching DDL, not production migration/drift integration.

Build the four completed packages with `python -m build`, then install their wheels plus this package's dev extras in a fresh virtual environment. Copy tests, demo.py, worker_process.py and pyproject.toml outside source. Run:

```sh
python -m pip check
python -m pytest -q tests
python -m mypy --strict demo.py worker_process.py
python demo.py --output leases.json
```

Supply ACADEMY_WORKER_DSN privately in the environment. The public suite has **59 cases: 35 offline and 24 PostgreSQL cases**. Without a DSN the 24 cases explicitly skip; skips do not evaluate database or process behavior. Signal evidence targets POSIX macOS/Linux. Tests use their own schemas and remove them. Demo saves actual JSON and reads installed metadata/resources. Do not invent versions for source-only execution.

The authored process fixture exits with os._exit(81) after committed claim and os._exit(82) after consumer acceptance but before settlement. The parent observes its tagged connections disappear, then observes actual DB-clock expiry and reclaims generation 2. Repeated acceptance preserves one inbox/aggregate application. A separate SIGTERM fixture signals only after seeing actual callback admission, lets that callback accept and settle, and verifies a second intent remains pending. Timing limits belong to the test harness, not the worker contract.

## Review and limits

Save actual tests/types/artifacts/JSON, explain two regressions, stale owners and time boundaries, and submit four manual criteria. A self checkbox or reported result does not award mastery.

Use this publisher instead of the previous row-lock publisher for these jobs; concurrently mixing both paths is unsupported. The unchanged HTTP POST still does not enqueue automatically. This trusted local PostgreSQL sink protects one local effect through inbox deduplication. A token cannot stop an expired worker from sending an external email/payment. Real broker acceptance, hostile-code isolation, wall-clock jumps, lease renewal, global capacity/fairness/jitter, production migrations/retention/redrive, database power loss and full deployment are not proved. Count bounds and cooperative SIGTERM cannot interrupt a blocked callback; hard process termination may leave committed effects and require expiry/replay.
