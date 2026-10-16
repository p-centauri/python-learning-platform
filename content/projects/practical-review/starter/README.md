# Composed Python practical review lab

Implement `decode_page`, `prepare` and `analyse` in operations.py. Complete scaffolding and 50 finite public cases are supplied; maintained solutions and assessor cases are excluded. This is a practical-review project with self/human criteria, not automatic expert certification.

## Build and install

Download/complete earlier starters. Build this eight-package composition in order: ingestion-package, feed-objects, typed-transforms, resource-scopes, bounded-offload, measured-cache, ingestion-service, practical-review. These are selected published units; later delivery/query/API packages retain their separate histories and contracts. For each completed starter run `python -m build` and copy its wheel into a private local wheel folder. The build creates a source archive and then a wheel from the archive.

Use Python 3.13 in a fresh environment, outside all source directories:

```sh
python -m venv .venv
.venv/bin/python -m pip install --find-links /absolute/path/to/wheels 'academy-practical-review-lab[dev]==0.1.0'
.venv/bin/python -m pip check
.venv/bin/python -m mypy --strict -p academy_practical_review
```

Copy `tests/` and `demo.py` into that outside directory. Run `.venv/bin/python -I -m pytest -q tests` and `.venv/bin/python -I -m mypy --strict demo.py`. Offline cases include actual owned thread/spawn workers and record **47 passed/three PostgreSQL skips**; skips do not prove store or real HTTP behavior.

Supply `ACADEMY_PRACTICAL_DSN` through private configuration for an explicitly disposable PostgreSQL 17 database. Never use the academy or production database, paste credentials into commands, or submit a DSN. Then all **50 public cases** should run without skips. Explicit fixture setup creates a generated service_002 schema and checks original head/metadata before removing only that schema. The service API has no new request/import DDL.

## Implemented contract

The service decoder keeps exact items/next_cursor and 0..1000000 values, <=32 ordered rows and a cursor naming the last returned item. Preparation borrows <=256 Datums, detects conflicts under every id/revision key, selects the highest revision per id and sorts <=64 immutable Items. Earlier Record/Row/Reading/Snapshot values require <=60000; refuse larger values at this adapter, never clamp or widen the old library.

Reporting takes <=256 exact integer request positions and creates ordered fingerprints over a frozen copied batch. Baseline computes each request. Candidate uses the old single-caller LRU, capacity eight and namespace/id/revision keys, fresh on every invocation. A 128-round SHA-256 component is a stated synthetic CPU workload, not a security protocol. Output order and values stay equal. Cache count bounds do not guarantee arbitrary bytes, freshness or concurrent safety.

The supplied async collector borrows a trusted configured client, uses the old permission-scoped route, reads <=eight pages with <=8192 decoded bytes each, closes response streams on cancellation/errors and leaves the client to its owner. Independent HTTP pages do not promise a shared database snapshot. The fixed fixture stops writes before collecting.

## Profile and review

Create your own bounded `review-case.json` using REVIEW_TASK.md. Run:

```sh
.venv/bin/python -I -m pytest -q tests
.venv/bin/python -I demo.py --case review-case.json --output practical.json
```

The installed demo observes actual loopback service writes, duplicates/conflict rollback, permissions and four async pages for 128 facts. It profiles latest reporting separately: 32 selected items, 152 requests with eight hot ids repeated sixteen times plus 24 cold requests. Equivalent baseline/cached outputs give 152/32 computations and 120 hits. The cyclic 32-id/two-pass distribution gives 64/64 computations and zero hits. It records raw wall/CPU intervals, actual profile call counts, separate Python allocation observations and actual prior thread/spawn file ownership. No speed, RSS or whole-service-throughput threshold is a pass condition. Borrowed tracers are refused; owned server/files/pools/schemas are cleaned.

Submit an original case and regression, exact package versions/revision/commands, public results, saved JSON and decision note. Preserve old HTTP/domain/warning/ownership behavior. Four criteria connect all seven advanced review dimensions. Originality, adequacy and tradeoffs need manual review. The academy serves this ZIP and stores reported evidence; it never executes your uploaded package. Public deployment, hostile memory/load bounds, hard deadlines and expertise remain outside this finite proof.
