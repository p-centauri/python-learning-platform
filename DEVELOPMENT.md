# Development

## Requirements and startup
Use Python 3.13+ and Node 22+. Run commands from the repository root unless noted.

```sh
make setup
make dev
```

`make setup` creates `.venv`, installs API runtime/check dependencies, and installs frontend packages from `package-lock.json`. `make dev` migrates and seeds the database before starting the API at `127.0.0.1:8000` and Next.js at `127.0.0.1:3000`. Ctrl+C stops services started by that script. If runner setup exists, it also starts the separate runner. Do not run this and the default Compose frontend on port 3000 simultaneously.

The local database is `apps/api/academy.db`, ignored by Git. No accounts are seeded. Create an account in the UI. Browser tests create separate test accounts with unique emails; they do not impersonate a real user.

If another Python interpreter is needed, run `PYTHON_BIN=/absolute/path/to/python bash scripts/dev.sh`. The script otherwise uses the repository's virtual environment. The API process currently needs a restart after Python code changes; Next.js reloads frontend changes.

## Isolated coding runner

Docker Desktop must be running. Enable the local runner once:

```sh
make runner-setup   # pull the two digest-pinned images; generate private .local/runner.env
make verify-runner  # real isolation probes plus five behavioral test groups
make dev
```

`make dev` loads the ignored mode-0600 configuration and starts the runner on `127.0.0.1:9000`, alongside API/web. Execution stays disabled while startup verifies all 13 isolation probes. If the app was already running before setup, stop its own processes and restart with `make dev` so the API loads the runner configuration. Do not start two services on the same ports. Standalone worker: `make runner`; it requires `.local/runner.env` and the pulled images.

Open `/coding`. Draft saving and history work without Docker; running checks requires a verified worker. Source is limited to 12,000 characters / 16 KiB UTF-8, eight recorded runs per ten minutes and one active worker job. A busy worker returns a retry message. No third-party package installation or network access is allowed. All expected values remain outside learner containers; private inputs/outputs are withheld from feedback. Passing does not increase mastery. If a cleanup/environment failure disables the worker, fix Docker and restart the worker to verify again.

Never expose port 9000 or copy the service token into browser code, learner containers or logs. The API has no Docker socket. Keep the trusted Docker controller local; public deployment needs the additional review in [ADR 0013](docs/adr/0013-isolated-coding-and-sql-runner.md). Runner tests require no active learner jobs and create/remove only containers with their own exact profile label. Full academy Compose verification is recorded in ADR 0042; use [OPERATIONS](docs/OPERATIONS.md) for the separate database and private Desktop worker configuration.

## Database and content
The API reads `apps/api/.env` when run from that folder. Set `DATABASE_URL` there to connect to a separate PostgreSQL development database. Copy configuration values from `.env.example` as appropriate. Compose reads the root `.env` and injects its own database URL.

```sh
make migrate
make seed
```

Content lives in `content/catalog.json` and `content/lessons/*.md`. `content/lesson-interactions.json` contains guided checkpoints, diagrams and glossary terms; it is API-only because checkpoint keys are private. New substantive checkpoint edits require a new version; stored feedback remains pinned. Seeding is repeatable and preserves learner state. Restart the API after editing content because the content bundle is cached in-process.

Create migrations from `apps/api` using `../../.venv/bin/python -m alembic revision --autogenerate -m 'describe change'`. Inspect generated migrations. Never replace existing migrations to hide schema changes.

## Checks
```sh
make test        # 232 content, domain and API behavioral tests
make verify-backups # three real backup/restore safety checks
make lint        # Ruff + strict TypeScript checking
make build      # production Next.js build
make format     # Ruff + Prettier
docker compose config --quiet
```

With the application running and Google Chrome installed:

```sh
cd apps/web
npm run test:e2e
```

Playwright uses a temporary Chrome profile. Screenshots and failure traces are written under `apps/web/test-results/`, ignored by Git. Set `E2E_BASE_URL` to target a different local test deployment. Avoid running these tests against real shared learning data: they deliberately create test accounts and attempts.

The 26 browser journeys include two guided-lesson flows (keyboard/fragment navigation, saved feedback, failure retry and glossary) and two recall flows. The delayed-check journey uses `tests/fixtures/age_review_source.py` to age only newly registered `recall-e2e-…@example.com` practice fixtures in the local SQLite file. This test requires the host SQLite deployment; it simulates a due schedule without changing real learner timestamps or providing a public clock-control route. API tests use isolated temporary databases and patched clocks. Recall needs no Docker; existing coding journeys require the verified worker.

CI is configured to run backend/backup-safety tests, migration drift checks, lint, npm audit, production frontend build, clean ingestion-package verification and a separate real Docker runner suite. The new remote runner job has not yet been observed in CI. Browser tests are presently local; CI browser orchestration remains a hardening task.

## Security checks
```sh
.venv/bin/python -m pip_audit
cd apps/web
npm audit
```

These require network access. A clean audit is evidence about known dependency advisories, not a substitute for an application security review. Top-level Python runtime dependencies are pinned; a fully hashed cross-platform dependency lock is future hardening work.

## Implementation conventions
Use feature components and typed API responses. Server-side services own grades and mutations. Do not import server content/answer keys into frontend bundles. Use a transaction-scoped SQLAlchemy session and authorize every learner-owned query. Avoid running a production build concurrently with frontend edits when checking generated TypeScript types.

## Local ingestion-package verification

`make verify-ingestion` builds the trusted maintainer reference as source archive and wheel, installs the wheel with its declared runtime dependencies into a fresh temporary virtual environment, then runs 28 offline tests, pip check, resource checks and both installed commands outside source. It never evaluates uploads or executes in the API. Runtime installation needs your configured package index; use `.venv/bin/python scripts/verify_ingestion_package.py --wheelhouse /absolute/path/to/wheels` for a complete pre-provisioned offline wheelhouse. Normal `make test` performs the authored runtime/type/lint/build checks without dependency downloads. Build tools are pinned in requirements-dev.txt and the starter.

The enlarged browser suite can reach the actual signup limit (20 auth requests per IP per minute). The retention registration helper respects a 429 Retry-After once, extending that test’s timeout. Authentication is not bypassed or weakened. Browser verification also covers the new eight-lesson path, glossary/recall privacy, authenticated download, saved project drafts and mobile overflow.

## Feed policy maintainer checks

`make verify-feed-policy` builds both maintained local packages, installs the wheels and pytest 9.0.3 into a fresh temporary environment, runs 49 offline public cases outside source, and checks quiet imports, the typing marker, the demo and real HTTPX fake-transport composition. It also strictly type-checks the protocol/adapter integration. Use `.venv/bin/python scripts/verify_feed_policy.py --wheelhouse /absolute/path` for a complete offline dependency wheelhouse. Setup otherwise needs the configured package index. This is trusted authored reference verification, never an evaluator for learner uploads. CI includes the command; remote runs have not been observed locally.

## Async-feed maintainer checks

`make verify-async-feeds` builds the maintained async and policy packages, installs their wheels plus pytest 9.0.3 in a fresh temporary environment, runs 75 public cases outside source, and checks quiet import, py.typed and the installed offline demo. A strict-typed HTTPX async opener composes real streamed records with the prior selector and proves response cleanup/client reuse. Use `.venv/bin/python scripts/verify_async_feeds.py --wheelhouse /absolute/path` for a complete offline dependency wheelhouse; otherwise setup needs the configured index. Tests use Events and an outer deadlock watchdog, not an async pytest plugin. Only trusted authored code runs. CI includes the verifier; remote execution has not been observed locally.

## Feed-object maintainer checks

`make verify-feed-objects` builds the maintained ingestion and object packages, installs the wheels and pytest 9.0.3 in a fresh temporary environment, and runs all 50 object cases outside source without PYTHONPATH. It checks pip consistency, quiet import, packaged typing marker and the installed demo, and strictly type-checks/runs an offline adapter from earlier ingestion Records to immutable Reading/Snapshot values. The object library has no third-party runtime dependencies; the adapter's prior ingestion wheel retains HTTPX. Use `.venv/bin/python scripts/verify_feed_objects.py --wheelhouse /absolute/path` with a complete offline wheelhouse; otherwise installation needs the configured index. CI includes this trusted-code check, but remote execution remains unobserved. No learner uploads execute.

## Typed transformation maintainer checks

`make verify-typed-transforms` builds the maintained ingestion/object/typing source archives and wheels, installs them plus pytest 9.0.3/mypy 2.3.1 in a fresh temporary environment, and runs 47 runtime cases outside source without PYTHONPATH or MYPYPATH. It separately checks one positive assert_type file and ten isolated rejected-call fixtures, requiring the intended diagnostic rather than any failure. Fixtures are inspected statically, never executed. Pip consistency, quiet import, typing marker/import location, installed demo and a strict-typed offline prior-record/snapshot adapter must pass. The new runtime uses the standard library; the prior ingestion wheel keeps HTTPX. Use `.venv/bin/python scripts/verify_typed_transforms.py --wheelhouse /absolute/path` with a complete wheelhouse; otherwise installation needs the configured index. Normal `make test` checks source/reference/type/lint/build behavior without dependency installation. CI includes the installer; remote execution remains unobserved.

## Resource-scope artifact verification

Run make verify-resource-scopes to build maintained ingestion/object/typing/resource source archives and wheels, install freshly with pytest 9.0.3/mypy 2.3.1, and run 54 resource cases outside source without PYTHONPATH/MYPYPATH. Pip check, quiet import, installed py.typed/import path, demo and strict-typed prior-value composition must pass. The new runtime uses only the standard library. scripts/verify_resource_scopes.py --wheelhouse /absolute/path uses a complete offline wheelhouse; otherwise the configured index is needed. CI includes this trusted-code verifier; remote execution remains unobserved. No learner uploads execute.

## Installed thread/process reference verification

Run make verify-bounded-offload to build maintained ingestion/object/typing/resource/offload source archives and wheels, install freshly with pytest 9.0.3/mypy 2.3.1, and run 66 public cases outside source without PYTHONPATH/MYPYPATH. Pip check, quiet import, installed py.typed/import path, guarded real-process demo and strict-typed prior-package composition must pass. The new runtime is standard library only. scripts/verify_bounded_offload.py --wheelhouse /absolute/path accepts a complete offline wheelhouse; otherwise the configured index is needed. CI includes this trusted-code verifier; remote execution remains unobserved. No learner uploads execute.

Save process examples as guarded importable scripts. A running future cannot be cancelled by Future.cancel, and result(timeout) does not stop it. Keep the caller file scope outside the owned batch, including failure shutdown. Public test Event deadlines detect broken fixtures and do not establish worker execution deadlines.

## Installed measurement/cache reference verification

Run make verify-measured-cache to build maintained ingestion/object/typing/resource/offload/measurement source archives and wheels, install freshly with pytest 9.0.3/mypy 2.3.1, and run 61 cases outside source without PYTHONPATH/MYPYPATH. Pip check, quiet import, installed py.typed/path, actual timing/profile/allocation demo and strict-typed supported old/new caller composition must pass. The new runtime is standard library only.

Use scripts/verify_measured_cache.py --report-output /absolute/path/report.json to preserve actual installed observations; saved JSON must parse back exactly. --wheelhouse /absolute/path supports a complete pre-provisioned offline wheelhouse. CI runs the trusted-code verifier; remote execution remains unobserved. The demo also supports --output measurement.json.

Samples/counters/output-equivalence are behavior checks, without faster-than or fixed-byte gates. Report workload/state/order, separate wall/CPU and run profiling/tracing separately. The demo owns fresh tracemalloc scope; never stop/reset application-owned tracing from an ordinary library. No learner uploads execute.

## Installed ingestion-persistence reference verification

Run `make verify-ingestion-persistence` with Docker running and the pinned PostgreSQL image available (`make runner-setup` pulls the same digest). It builds four maintained source archives/wheels, installs freshly with driver/pytest/mypy/stubs, checks installed schema/typing resources and quiet import, runs all 57 cases against an owned disposable PostgreSQL 17 container and verifies actual demo JSON plus a strict-typed prior Record/Row/Snapshot adapter. The helper uses a unique container/network, tmpfs data and loopback ephemeral port; private temporary credentials stay unprinted. Owned resources are removed on completion. This is trusted maintainer work, never learner upload execution.

`scripts/verify_ingestion_persistence.py --report-output /absolute/path/persistence.json` saves actual observations with exact JSON readback. `--wheelhouse /absolute/path` supports fully provisioned offline Python dependencies, with the pinned image already present. CI includes this verifier; remote execution remains unobserved. Public learners supply `ACADEMY_PERSISTENCE_DSN` to an explicitly disposable PostgreSQL database and run the supplied demo/tests; without it the 25 database cases skip and persistence remains unevaluated. Never print or submit a DSN/password. No academy migration/runtime dependency change is required; only driver stubs were added to development requirements.

## Ingestion-service artifact and PostgreSQL verification

Run `make verify-ingestion-service` with Docker running and the same digest-pinned PostgreSQL image already available (`make runner-setup`). The trusted verifier builds five source archives and wheels from their sdists, installs them into a fresh environment, checks pip consistency, quiet import, packaged migrations/typing markers and strict installed demos/adapters. It runs all 70 public cases against its own disposable PostgreSQL 17 container, compares actual ASGI/transaction/migration JSON, composes earlier Record/Row/Reading/Snapshot contracts, and starts/stops the supplied installed loopback TCP server. Only trusted authored references are executed; this is never learner code in the academy API.

`.venv/bin/python scripts/verify_ingestion_service.py --report-output /absolute/path/service.json` saves actual observations and parses them back exactly. `--wheelhouse /absolute/path` supports a complete offline Python wheelhouse with the pinned image already present. The helper owns a unique container/network, tmpfs database, loopback ephemeral port and unprinted private credentials; cleanup targets only its own resources. CI includes this verifier, but a remote run has not been observed.

Learners download the nineteen-file starter from Projects, implement its three functions and follow its README with Python 3.13+ and an explicitly disposable PostgreSQL database. `ACADEMY_SERVICE_DSN` stays private. Without it, 27 database cases explicitly skip; that does not evaluate persistence. The guarded demo writes actual JSON. `serve.py --port 8010` requires an already migrated disposable schema and private caller-generated `ACADEMY_SERVICE_TOKENS`; it binds loopback and never runs migrations automatically. The DSN adapter accepts explicit local host/dbname/user and supported port/password/options only. Other options are rejected; provider/TLS deployment is a separate unit.

Runtime pins match the academy: FastAPI 0.141.1, Starlette 1.6.0, Pydantic 2.13.5, SQLAlchemy 2.0.43, Alembic 1.16.5 and psycopg2-binary 2.9.10. HTTPX 0.28.1 and Uvicorn 0.35.0 support local tests/server; pytest, mypy/stubs, Ruff and artifact builders are development tools. No academy dependency or schema change is required. A pool wait limit is not a request deadline, a head marker is not a drift check and passing a serial local lab is not concurrency/deployment proof (ADR 0025).

## Competing-ingestion artifact and PostgreSQL verification

Run `make verify-competing-ingestion` with Docker and the same digest-pinned PostgreSQL image available. The trusted verifier builds the maintained prior service and new extension from real source archives/wheels, installs both into a fresh environment, checks pip consistency/quiet import/typing resources, runs all 70 public cases outside source on its own disposable PostgreSQL 17 container and verifies actual demo JSON/readback plus previous-API permissions. No PYTHONPATH/MYPYPATH fallback, learner upload or academy database is used. The existing private runner is unchanged.

`.venv/bin/python scripts/verify_competing_ingestion.py --report-output /absolute/path/competition.json` saves actual observations. `--wheelhouse /absolute/path` supports a complete offline Python wheelhouse with the image already present. The shared helper owns a unique container/network, tmpfs database, ephemeral loopback port and private temporary credentials, removing only its own resources. CI invokes the verifier; remote results remain unobserved.

Learners complete/build the previous service wheel, install it locally, then download/finish the thirteen-file extension. These academy packages are not published on PyPI. Supply private `ACADEMY_COMPETITION_DSN` for an explicitly disposable database; without it the seventeen database cases skip. Fixtures/demo create/drop unique schemas. The actual deadlock fixture requires server deadlock_timeout below 2000 ms (default 1000), checks this and does not change privileged settings. READ COMMITTED delivery uses the prior service schema/migrations; stronger-isolation demonstrations borrow separate experimental connections and do not change the engine default. No academy dependency/schema change is needed.

The demo separates real blocker/snapshot/SQLSTATE/attempt facts from modeled response loss after actual commit. Server statement/lock limits, event/barrier/poll bounds and joined cleanup are separate; none is a hostile hard whole-job deadline. Missing reconciliation is not rollback proof. Full public deployment, stress/fairness, crash recovery/backups and exactly-once effects remain unevaluated.

## Installed durable outbox verification

`make verify-durable-outbox` runs scripts/verify_durable_outbox.py; `--report-output` saves actual JSON, and `--wheelhouse` supports a complete prepopulated offline wheelhouse with the pinned PostgreSQL image already available. Three maintained source archives/wheels build from sdists and install freshly without PYTHONPATH/MYPYPATH. Pip check, quiet import, packaged schema.sql/py.typed, installed demo/crash-worker types, 67 real PostgreSQL cases and exact JSON readback pass. CI is configured, not remotely observed.

The existing owned disposable PostgreSQL helper supplies private credentials and bounded tmpfs/container resources, and removes only its own container/network. Child fixtures terminate only the spawned authored worker. They observe worker exits/replay while PostgreSQL remains alive, not broker acceptance or database power loss. Academy runtime/schema, existing runner contracts and auth are unchanged. The earlier local wheels must be completed/installed first; these packages are not on PyPI. Use explicit one-time additive setup in disposable schemas only; the prior Alembic drift check sees these extra tables. See ADR 0027.

## Leased-worker artifact and PostgreSQL verification

Run `make verify-leased-worker` with Docker and the same digest-pinned PostgreSQL 17 image. The trusted verifier builds the completed service, competition, outbox and worker packages from source archives/wheels, installs them in a fresh environment and runs copied tests outside source. It checks pip consistency, quiet imports, packaged SQL/typing markers, strict installed demo/process types, all 59 public cases without skips and actual JSON/readback with prior API permissions. Use `--report-output` with scripts/verify_leased_worker.py to save the actual non-secret report. No PYTHONPATH fallback, invented metadata or learner execution.

The worker starter has three unfinished functions; 35 offline cases and 24 real PostgreSQL cases. Private ACADEMY_WORKER_DSN config belongs to an explicitly disposable database. Explicit setup follows prior service/outbox setup; never use shared production data. POSIX process evidence observes two abrupt exits, vanished tagged connections, actual expiry/reclaims and cooperative SIGTERM. Fixtures manipulate some test-only timestamps to evaluate finite schedules; they label those models. The owned database helper removes its limited tmpfs container/network. No broker, power-loss, hostile-code, global admission or hard shutdown claim. Production Next standalone checks must stage .next/static beside the actual .next/standalone/server.js before starting it (ADR 0028).

## Stream delivery artifact and live verification

Run `make verify-stream-delivery` with Docker and both pinned images available: the existing PostgreSQL 17 digest and redis@sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952 (observed Redis 7.4.2). `scripts/verify_stream_delivery.py --report-output <private-output-path>` builds five source archives/wheels, installs into a fresh environment and verifies quiet imports/typing resources, pip consistency, strict installed demo/process types, all 74 public cases without skips, real JSON/readback and earlier service permissions. No source fallback or learner execution.

The helper owns a password-protected loopback broker, selected restart-stable port, AOF volume, memory/CPU/PID limits and generated private configuration. Redis uses appendonly yes, appendfsync always and noeviction. XADD/WAITAOF share one dedicated physical connection. A temporary PostgreSQL schema/container holds facts, inbox/effects and worker state. All owned resources are removed. Root development requirements add redis==6.4.0; academy runtime requirements/Compose/runner remain unchanged.

The starter has three unfinished functions and 59 offline/15 live cases. ACADEMY_STREAM_DSN and ACADEMY_BROKER_URL are private and must refer to disposable stores; the owned ACADEMY_BROKER_CONTAINER enables the controlled restart fixture. Without both stores the live cases skip honestly. Tests only delete their generated stream key, never FLUSHDB. Actual child exits and idle/lease observations remain separate from fixture models and controlled restart from power-loss/failover. Stage production static files beside the actual standalone server before browser checks (ADR 0029).


## Installed delivery migration verification

Run `.venv/bin/python scripts/verify_delivery_schema.py --report-output .local/schema-20261004/installed-schema.json` or `make verify-delivery-schema`. The caller creates the report directory. Build six completed sources/wheels from sdists, install freshly without PYTHONPATH/MYPYPATH, check pip/resources/quiet import/strict types and run all 44 cases on owned digest-pinned PostgreSQL/Redis. The verifier removes its own store resources. No API/frontend runtime dependency or academy migration change.

Offline maintained checks are 25 passes/19 explicit skips; strict source/demo types cover ten files. The installed demo preserves timestamped old service facts, explicitly adopts matching records, composes real broker delivery, detects missing-index drift while head remains true, observes destructive rollback loss/re-upgrade replay and old service API 401/403/200 with /ready 503. Save actual JSON and explain limited autogenerate coverage. Never use production or the academy database for learner rehearsal.


## Installed delivery recovery verification

Run `make verify-delivery-recovery` or `.venv/bin/python scripts/verify_delivery_recovery.py --report-output .local/recovery-20261005/installed-recovery.json`. The verifier builds seven maintained source/wheel artifacts, installs them freshly without source-path fallbacks, checks pip/resources/quiet import/strict package and demo types, then runs 36 cases with no skips on owned digest-pinned PostgreSQL/Redis. It saves and reads actual JSON and removes its helper containers, networks and AOF volume. Remote CI is configured, unobserved. Never use this maintainer verifier to run learner uploads.

The twelve-file authenticated starter has three unfinished functions and a supplied Lua guard. Configure private ACADEMY_RECOVERY_DSN/ACADEMY_BROKER_URL only for disposable stores; otherwise 22 cases explicitly skip. Keep Event/generation/policy and deduplication history intact. Freeze group topology/rewinds before acknowledging exact payload loss; PostgreSQL rollback cannot undo Redis deletion. Details and commands are in the starter README and ADR 0031.


## Installed release verification

Run `make verify-delivery-release` or `.venv/bin/python scripts/verify_delivery_release.py --report-output .local/release-20261007/installed-release.json`. Eight completed source archives/wheels are built and installed outside source in a fresh environment. Pip/resources/quiet import/strict types precede all 33 cases on owned stores, actual CLI/loopback/SIGTERM and broker-composed JSON with readback. Missing-store source runs explicitly skip 18 cases. Expected operating failures emit finite reasons; programmer errors remain failures. Helpers remove their own stores/children. Never run uploads with this maintainer verifier; remote CI is configured but unobserved.


## Installed query analysis verification

Run `make verify-query-analysis` or `.venv/bin/python scripts/verify_query_analysis.py --report-output .local/queries-20261007/installed-queries.json`. The trusted verifier builds nine source/wheel packages, installs outside source, checks pip/quiet imports/typing and all six SQL resources, then runs all 36 cases on owned digest-pinned PostgreSQL. Five authored literal SQL examples are independently executed through the installed library owner. Actual 40,000-row baseline/indexed reports check ordered result equivalence and source metadata after fixture index removal. Missing-store source runs skip 13 cases. No Redis broker is needed for this query unit; prior dependencies remain installed unchanged. Helpers clean their owned PostgreSQL resources. Never run learner uploads with this verifier; remote CI is configured but unobserved.


## Installed API-depth rehearsal

Five ordered lessons (python-http-validators through python-api-depth-evidence), ten original scenarios under separate API delivery contracts and complete guided/diagram/glossary/private recall layers connect to the API depth lab. Its authenticated fourteen-file starter has three unfinished functions, 51 public cases (39 offline/12 PostgreSQL) and four manual criteria. Nine freshly installed packages verify private conditional GET/permission ordering, framed raw-byte HMAC/freshness/strict events, atomic scoped receipts/readings, real competing duplicates/conflicts/rollback/lock timeout and compatible prior routes. The saved actual loopback HTTP report observes 200/304/change, 401/403/409/422/503/retry, committed counts and released connections. Reported tests and manual review do not award mastery (ADR 0034).

`make verify-api-depth` builds nine completed maintained archives/wheels, installs them outside source in a fresh environment, checks pip/import location/quiet imports/typing, runs all 51 cases against owned PostgreSQL 17.11 and verifies actual loopback HTTP JSON/readback/server/connection cleanup. `scripts/verify_api_depth.py --report-output /absolute/path/api.json` saves observations; `--wheelhouse /absolute/path` accepts a complete dependency wheelhouse. Without it, configured package-index access is needed. Learners supply private `ACADEMY_API_TEST_DSN` to an explicitly disposable store; offline runs report twelve skips rather than invent storage evidence. The academy never executes uploads. Configured CI includes the verifier; remote execution remains unobserved.


## Composed advanced Python practical review

Five lessons (`python-practical-contracts` through `python-practical-review`), ten original scenarios and complete guided/diagram/glossary/private recall layers connect to the Composed Python practical review lab. Its authenticated eighteen-file starter has three unfinished functions, 50 public cases (47 offline/three PostgreSQL) and four manual criteria covering all seven advanced review dimensions. Eight freshly installed local packages compose strict old service pages, latest/conflict/domain adapters, immutable typed snapshots, response/resource ownership, bounded cache and actual thread/spawn workers. A stated 128-fact workload gives equivalent reporting outputs with 152/32 computations and 120 hits; a cyclic case gives 64/64 and zero hits. Actual cProfile call counts, raw wall/CPU intervals and Python allocation observations have no speed threshold. The original-case/regression/design task feeds fixed manual submissions and revisions. Maintainer fixtures and reported tests never establish learner originality, mastery or expertise (ADR 0035).

`make verify-practical-review` builds eight maintained source archives/wheels, installs outside source, checks pip/import/type boundaries and runs all 50 cases on owned PostgreSQL 17.11. `scripts/verify_practical_review.py --report-output /absolute/path/practical.json` saves actual HTTP/profile/worker evidence plus a clearly labelled maintainer example; `--wheelhouse /absolute/path` uses a complete dependency wheelhouse. Otherwise configured package-index access is needed. Learners set private `ACADEMY_PRACTICAL_DSN` only for an explicitly disposable store; offline runs skip three store cases. Configured CI includes this verifier; remote execution is unobserved.


## Offline model contracts

Six lessons (`model-request-contracts` through `model-contract-evidence`), twelve original scenarios under separate **Model call contracts** and complete guided/diagram/glossary/private recall layers connect to the Model contracts lab. Its authenticated fourteen-file starter has three unfinished functions, **84 offline public cases** and four manual criteria. A clean installed standard-library package normalizes two invented provider formats; checks pinned model/prompt/schema, copied complete-envelope context/output admission, strict complete/refused/incomplete proposal/usage variants; and reserves fictional credits before attempts, settles only valid usage, retains unknown reserves and stops at cost/step/one cooperative deadline boundaries. Actual waiting fixtures verify timeout cleanup and propagated external cancellation. Installed JSON records eleven finite cases without raw prompts/refusal reasons/exceptions. No real model, network, current pricing, provider conformance or semantic quality is claimed (ADR 0036).

`make verify-model-contracts` builds the maintained source archive/wheel, installs outside source in a fresh environment, checks pip/quiet import/path/py.typed/strict types and runs all 84 cases without skips. `scripts/verify_model_contracts.py --report-output /absolute/path/model.json` saves checked installed demo JSON; `--wheelhouse /absolute/path` accepts a complete dependency wheelhouse. Otherwise configured package-index access is needed. Model calls stay offline; no DSN, provider key, Docker or paid request is needed for this verifier. Configured CI includes it; remote execution remains unobserved.


## Scoped retrieval contracts

Six lessons (`retrieval-chunk-identities` through `retrieval-evidence`), twelve original scenarios under separate **Scoped retrieval contracts** and complete guided/diagram/glossary/private recall layers connect to the Scoped retrieval lab. Its authenticated fifteen-file starter has three unfinished functions, **83 public cases** and four manual criteria. The installed standard-library package preserves complete chunk keys/character offsets/digests, validates model/version/dimensions/finite nonzero vectors, chooses latest revisions before trusted tenant/group/activity/metadata filters, then computes exact cosine or simple ASCII token-set Jaccard ranking with full-key ties. Requested-k precision, labelled recall and first-relevant rank use explicit denominators; no-label cases have null recall/rank and separate unwanted-hit counts. Four computed reports use an original 12-revision/15-chunk/nine-query development fixture with hand-supplied six-dimensional vectors. No real embedding model, ANN/database index, held-out quality, durable document lifecycle or automatic mastery is claimed (ADR 0037).

`make verify-retrieval` builds the maintained source archive/wheel and installs outside source in a fresh environment. It checks pip/quiet import/location/py.typed/fixture.json/strict types, all 83 cases without skips and four actual ranking reports with saved JSON readback. `scripts/verify_retrieval.py --report-output /absolute/path/retrieval.json` saves the checked report; `--wheelhouse /absolute/path` accepts a complete dependency wheelhouse. Otherwise installation needs configured package-index access. Lab calls need no network/model/key/DSN/Docker. CI includes the command; remote execution is unobserved.


## RAG continuation (2026-10-11)

Run `make verify-rag`, or `.venv/bin/python scripts/verify_rag.py --report-output .local/rag-report.json`. The verifier builds all three source archives and wheels, installs them into a fresh environment outside source, checks pip/quiet typed imports, runs 70 installed and 70 maintained-source RAG cases plus the prior 84 model and 83 retrieval cases, strict-checks package/demo code and computes/saves/readbacks the lifecycle report. `--wheelhouse PATH` supports a supplied dependency wheelhouse; see `--help` for the full command. Installation uses the configured index unless dependencies are supplied; lab generation/retrieval calls are offline. No Docker, PostgreSQL DSN or provider token is needed for this verifier. Use a separate local SQLite path, never `apps/api/academy.db`. The learner starter deliberately leaves `publish`, `prepare` and `answer` unfinished; maintained reference files are excluded from the authenticated ZIP.


## Tool-use continuation (2026-10-11)

Run `make verify-tools`, or `.venv/bin/python scripts/verify_tools.py --report-output .local/tools-report.json`. It builds all four source archives/wheels, installs outside source, checks pip/quiet typed imports and strict packages/demo, runs 81 installed/source tool cases plus existing 84 model/83 retrieval/70 RAG cases, and computes/saves/readbacks tools.json. `--wheelhouse PATH` supports supplied dependency wheels; installation otherwise uses the configured index, while lab calls are offline. No Docker, PostgreSQL DSN or provider token is needed for this verifier. Separate source/note database paths must never be the academy database. Learner decode_proposal/execute/run stay unfinished; maintained reference files are excluded from the authenticated ZIP.


## Final step-six evaluation (2026-10-12)

Run `make verify-ai-evaluation` or `.venv/bin/python scripts/verify_ai_evaluation.py --report-output .local/release-report.json`. Five archives/wheels install outside source; all 54 evaluation and prior 84 model/83 retrieval/70 RAG/81 tool cases pass, with typed resources/packages/demo and actual saved comparisons. `--wheelhouse PATH` supports supplied dependencies; installs otherwise use the index while lab calls are offline. No Docker, provider token or PostgreSQL DSN is needed for this verifier. `make audit-learning-paths` checks published layers/paths/manifests; use `--baseline PATH --report-output PATH` with the script for preserved-definition evidence. Syntax audit does not execute all older excerpts. Maintained reference functions are excluded from the authenticated starter.

## Verify comprehensive assessment

Run `make test`, `make lint`, `make build`, `make audit-learning-paths` and `make verify-comprehensive` (Docker required). The last verifies thirteen isolation probes, 23 maintained repair cases and eight deliberately failing public starter cases, using fresh containers. Run it after other runner jobs/startup probes finish because the profile inventory check intentionally rejects leftover/overlapping containers. Three portfolio build packs are deliberate service implementation boundaries, not reference products. Browser coverage is `tests/comprehensive.spec.ts` plus original Python levels. Keep credentials/private DB backups out of logs; see ADR 0041 and STATUS for exact current scope.
