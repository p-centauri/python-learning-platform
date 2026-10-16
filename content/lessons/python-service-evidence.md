## The idea in plain language

Download the local ingestion service starter after the persistence unit. Three functions remain unfinished: authorize, ingest and read_page. The supplied routes, strict models, ORM metadata, two migrations, local server and tests connect input, permissions, storage and public output. No learner code runs in the academy API.

Use a separate disposable PostgreSQL 17 database and unique schema. No built-in credential exists. Keep caller-generated tokens and DSNs private. If the database environment variable is absent, PostgreSQL cases explicitly skip; an offline green result proves only the offline checks. The maintained reference runs all 70 cases against actual PostgreSQL.

Collect evidence from multiple boundaries. Strict-input/configuration cases run locally. Database API tests show first/repeated receipts, whole-batch rollback after a 409 or 503 response, separate observers, permission/body/cursor rejection, bounded pages, caller-state preservation and pooled resource return. A pre-commit injected error verifies success ordering, while uncertain real commit communication remains a different failure model.

Migration cases start from revision 1 with saved data, upgrade/head-check, downgrade/re-upgrade, identify timestamp metadata loss, verify direct SQL constraints and gate readiness. The demo preserves actual versions/statuses/page/rollback/migration observations. HTTPX ASGI transport tests app behavior without DNS/TLS. A separate installed TCP check starts/stops the supplied loopback server and authenticates requests with private generated credentials.

Build the source archive then wheel, install freshly outside source and run copied tests/demo without PYTHONPATH/MYPYPATH. The installed package must contain typing marker and all migration files. A typed adapter maps prior Record/Row/Reading values into Datum without changing the earlier packages. Quiet import neither starts a server nor connects/migrates a database.

Four manual criteria distinguish HTTP/input/output, permission boundaries, transaction/failure ownership and migration/installed evidence. Add two meaningful regressions and explain query/body/time limits, changed-data pagination and uncertain commits. Finite authored cases and reported/manual review do not award mastery or certify expertise. Competing transactions/retries, workers/outbox/recovery, broader HTTP/PostgreSQL depth, deployment and applied AI remain later units.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
evidence = {"offline": "validation", "postgres": "transactions", "tcp": "local server"}
print(len(evidence))
print("reported output needs review")
```

## Guided practice

Distinguish offline, PostgreSQL, ASGI, TCP, migration and manual-review evidence. Identify what each check cannot establish.

## Independent practice

Finish the three functions, run actual tests/demo/server and clean installation, add regressions and submit design/failure evidence.

## Check your work

No invented result or public-deployment/skill certification claim. Record skipped cases and private configuration honestly.

[Download the ingestion service starter](/api/projects/python-ingestion-service/starter), then open the [project checklist](/projects#python-ingestion-service) and [submission workspace](/projects/python-ingestion-service/submissions).

Continue to [What a PostgreSQL transaction can see](/lessons/python-pg-snapshots).
