# API depth lab

Implement three functions in `src/academy_api_depth/operations.py`: `matches`, `verify`, `accept`. The package scaffolding and public tests are supplied. There is no completed reference in this download. Finite tests and self/human review do not certify expertise.

## Install the completed dependency chain

Download and complete earlier project starters. Build in order: ingestion-service, competing-ingestion, durable-outbox, leased-worker, stream-delivery, delivery-schema, delivery-recovery, delivery-release, api-depth. Each declares its pinned predecessor. Use a fresh Python 3.13 environment and a local wheel folder. For each completed starter run `python -m build`; copy its wheel into the wheel folder. Build performs a source archive then a wheel from that archive. This lab does not require query-analysis or change its package.

From an empty directory outside all source trees:

```sh
python -m venv .venv
.venv/bin/python -m pip install --find-links /absolute/path/to/wheels 'academy-api-depth-lab[dev]==0.1.0'
.venv/bin/python -m pip check
.venv/bin/python -m mypy --strict -p academy_api_depth
```

Copy this starter's `tests/` and `demo.py` into that empty directory. Run `python -I -m pytest -q tests` and `python -I -m mypy --strict demo.py` using the new environment. Offline runs have 39 cases and twelve explicit PostgreSQL skips. They do not evaluate storage or HTTP concurrency.

## Actual store and requests

Set `ACADEMY_API_TEST_DSN` privately to an explicitly disposable PostgreSQL 17 database. Never use academy state or production. Do not paste credentials into commands, reports or submissions. Supply it through private local environment configuration, then run:

```sh
.venv/bin/python -I -m pytest -q tests
.venv/bin/python -I demo.py --output api.json
```

All 51 public cases should run without skips. The fixture creates a generated delivery_004 schema, explicitly adds the receipt table, then removes it and checks unchanged original source metadata before dropping the generated schema. No import/factory/request DDL exists. The caller owns the borrowed Engine.

The demo starts and stops an owned ephemeral loopback HTTP server. Its JSON records actual conditional requests, permissions, signatures, competing duplicate receipts, conflicts, stale/invalid input, a real lock timeout and retry, committed counts and released connections. It does not send traffic to an external provider. The static demo keys are disposable examples, never production credentials.

## Submit

Include artifacts/versions, exact commands and outputs, `api.json`, a new independent regression and a clear design explanation. Use the four published criteria. Explain private caching, uncertain commit/retry, raw-byte identity, local atomicity and external-effect limits. Preserve old API items/output/no-store/zero semantics and its standalone readiness expectation. See HTTP_CONTRACT.md for exact wire/status rules.
