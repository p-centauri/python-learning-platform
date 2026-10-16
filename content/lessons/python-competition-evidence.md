## The idea in plain language

Download the competing-ingestion starter after completing the prior ingestion service. Its installable package depends on that earlier local wheel. Three functions remain unfinished: classify_sqlstate, retry_ingest and reconcile. Public experiments and tests reuse the service's Datum, Session transaction and migrated PostgreSQL schema; the earlier package contract stays unchanged.

Use a separate disposable PostgreSQL 17 database. Each fixture/demo owns a unique schema and cleans only that schema. No academy data or shared credential is used. Without ACADEMY_COMPETITION_DSN, database cases explicitly skip. An offline green result cannot establish lock waits, deadlocks, snapshots, timeouts or commits.

Collect actual evidence: four observed insert races, statement versus transaction snapshots, SERIALIZABLE 40001 with a new decision, real inverse-key 40P01 with complete bounded retry, actual 55P03/57014 without replay, namespace/full-key reconciliation, transaction-local setting reset and pooled connection return. Record bounds and clean shutdown. Events/barriers organize the experiment; pg_blocking_pids and actual SQLSTATE establish database observations.

The supplied modeled acknowledgment-loss case commits real data, then simulates a missing response. Label it as modeled; do not call it a real network failure. In-flight reconciliation also shows why missing is not rollback proof. A separate existing-API check retains 401/403 and the chosen public output after extension writes.

Build source archives and wheels, install the completed prior service wheel and this wheel into a fresh environment outside source, and run copied tests/demo without PYTHONPATH/MYPYPATH. Quiet import must neither connect nor start an experiment. Save actual version/status/attempt/final-fact JSON, not a hand-written green summary. The academy records reported output and manual review; it never executes these packages or treats their results as mastery.

Four criteria distinguish visibility/wait observations, retry/ownership, reconciliation/permissions and installed evidence/limits. Add two meaningful regressions. This finite two-writer unit does not prove high-load fairness, arbitrary isolation correctness, hard total deadlines or durable recovery. Workers/outbox/crash replay, broader PostgreSQL/API depth, deployment and applied AI remain later work.

## Worked example

This local Python illustration explains one idea. The PostgreSQL lab supplies the actual database observations.

```python
evidence = {"observed": "database SQLSTATE", "modeled": "lost response"}
print(len(evidence))
```

## Guided practice

Label observed database events separately from controlled modeled failures and learner-reported output.

## Independent practice

Complete the three functions, run actual PostgreSQL/installed checks, add regressions and submit the four manual criteria.

## Check your work

Do not certify expertise or recovery from a finite fixture or a skipped database run.

[Download the competing-ingestion starter](/api/projects/python-competing-ingestion/starter), then open the [project checklist](/projects#python-competing-ingestion) and [submission workspace](/projects/python-competing-ingestion/submissions).

Continue to [Save the fact and publishing intent together](/lessons/python-outbox-atomicity).
