## The idea in plain language

Download the ingestion persistence starter after measurement/cache work. It is a separate installable package, with three unfinished functions: bounded input snapshot, transactional persistence and bounded read. It uses Psycopg 2 and PostgreSQL 17; the academy API only serves the fixed starter and stores reported evidence.

Use an explicitly disposable database and a generated unique schema. The public fixture owns setup/teardown; never use the academy or production database. Keep DSNs/passwords out of screenshots and submissions. Without ACADEMY_PERSISTENCE_DSN the PostgreSQL cases explicitly skip, which is not a passed persistence evaluation.

Build evidence across layers. Python cases check exact types, boundary values, frozen readings and one-pass borrowed input. PostgreSQL cases bypass constructors to observe actual NOT NULL/CHECK/foreign-key/unique failures. Batch tests show first and repeated counts, complete key distinctions, late whole-batch rollback, caller-state rejection and separate-connection visibility. The demo saves actual server/driver version, SQLSTATE, data and transaction observations.

A local editable import is not the installed artifact. Build a source archive and wheel, install in a fresh environment outside source, check packaged schema.sql/py.typed and run copied tests/demo there without PYTHONPATH/MYPYPATH. A strict-typed adapter maps earlier Record/Row values into Readings; it does not alter previous package contracts. The trusted maintainer verifier owns one disposable digest-pinned database container and removes its own resources.

Four manual criteria separate modeling, transaction/failure evidence, duplicate/bounded read behavior and installed integration. Add two meaningful failure regressions and explain uncertain commits, external effects and the append-only scope. Finite cases, reported output, reading and checklist completion do not award practical mastery or certify expertise.

This completes the first persistence unit. SQLAlchemy/FastAPI/Alembic integration, schema evolution, real service ingestion, competing transactions, worker retry/recovery, backups and deployment remain later units. A disposable lab is not verification of the full academy PostgreSQL deployment.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
report = {"observed": 3, "inserted": 2, "duplicates": 1}
print(report["observed"] == report["inserted"] + report["duplicates"])
print("reported evidence is not mastery")
```

## Apply it in the PostgreSQL lab

Run in the local starter after implementing its three functions and configuring a disposable PostgreSQL DSN as README explains. Record skipped cases honestly. Then copy public tests/demo outside source and verify a freshly installed wheel too.

```text
python -m pytest -q
python -m mypy --strict src demo.py
python -m ruff check src demo.py tests
python -m build
python demo.py --output persistence.json
```

## Guided practice

Choose evidence for input, database, transaction, artifact and reviewer boundaries. Distinguish skipped tests from evaluated behavior.

## Independent practice

Finish the lab, save actual JSON/output, build/install outside source and submit implementation/design/failure evidence for manual review.

## Check your work

No fabricated result, automatic mastery or full deployment claim. Explain remaining service/concurrency/recovery work.

[Download the ingestion persistence starter](/api/projects/python-ingestion-persistence/starter), then open the [project checklist](/projects#python-ingestion-persistence) and [submission workspace](/projects/python-ingestion-persistence/submissions).

Continue to [HTTP contracts & honest success responses](/lessons/python-http-api-contracts).
