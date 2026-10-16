# Deployment

The first user-authorized hosted core is running at **https://academy.45-141-22-101.sslip.io** (2026-10-16). [SERVER_DEPLOYMENT](docs/SERVER_DEPLOYMENT.md) is the concrete server runbook: separate fresh PostgreSQL/credentials, preserved carwash/Caddy, actual HTTPS/browser/persistence/restore checks and unavailable hosted execution pending a separate worker. This does not close the broader public acceptance checklist.

## Local Compose topology
`db` runs PostgreSQL 17. `db-setup` waits for its health check and prepares the restricted application role. `migrate` uses that role to apply Alembic migrations and seed content once. `api` starts after successful migration and checks the actual schema/database. `web` starts after API health is established and serves the Next.js standalone build on loopback port 3000.

```sh
docker compose up --build
```

To use another host port: `WEB_PORT=3001 docker compose up --build`. Also add that exact browser origin to `ALLOWED_ORIGINS` or mutations will be rejected. Browser cookies are host-scoped, not port-scoped; use distinct local hosts when running independent deployments concurrently.

`docker compose down` stops containers while preserving the named PostgreSQL volume. Do not use `down -v` unless intentionally discarding learning state. Preserve the database in backups; content is reconstructible from Git, learner attempts and notes are not.

The Next.js API destination is a **build argument** (`API_INTERNAL_URL=http://api:8000`) because rewrites are captured by the build. Changing a runtime environment variable alone does not retarget an existing image.

## Verification state
Full five-service Compose startup and API/web builds pass on Docker Desktop. Actual PostgreSQL auth/note/export/isolated coding work, non-root API/web, migrations/seed/restart, restricted-role flags and database-outage readiness/liveness are verified. Real 25-table/338-record archive restore and recovery/session races pass; SQLite 25-table/4,790-record restore and all original learner state remain preserved separately. See [OPERATIONS](docs/OPERATIONS.md), ADR 0042 and STATUS/PROGRESS for exact evidence and private configuration locations. This is local acceptance; no public production rollout is claimed.

## Public release requirements
See SECURITY.md. Place a trusted HTTPS reverse proxy in front, use Secure cookies and exact Origins, replace local credentials, add service/ingress resource limits and shared throttling, and test the hosting-specific incident/restore procedure. Local API mutations have a 256 KiB body cap and bounded hashing concurrency. Run migrations as a single deployment step. The API now separates database/schema readiness from process liveness; integrate those signals with the hosting platform.

No public hosting, external account provisioning or paid services were configured in M1.

## Runner deployment boundary
The verified coding runner uses the host development launcher and loopback port 9000. Default Compose keeps it unconfigured, so drafts/history work but execution is disabled. No Docker socket is mounted into the API or web. The private Docker Desktop bridge at `host.docker.internal:9000` was verified while the controller stays on host loopback; use the mode-0600 helper configuration in OPERATIONS. Compose cannot use its own `127.0.0.1` for the host controller. Do not expose the powerful controller. A separately reviewed private worker topology, admission controls and stronger public isolation are prerequisites for production execution. See ADR 0013.


## Bounded installed lab release

The [local operating runbook](content/projects/delivery-release/starter/RUNBOOK.md) is verified for the installed disposable lab, not the whole academy. It orders private configuration, stopped writers, explicit prepare/check, loopback serve, health/readiness/business observations, SIGTERM/reaping and a named destructive rollback. delivery_003 loses worker/job state; service_002 also loses delivery/deduplication history while service facts/timestamps remain. Re-upgrade restores empty structures, not deleted history. The new release expects delivery_004 and preserves previous API routes/permissions. Full academy Compose and isolated backup restoration are verified separately in ADR 0042; public deployment and zero-downtime remain open.


## Query/index experiments are local rehearsal

The [query lab instructions](content/projects/query-analysis/starter/README.md) create owned source/report schemas and add/drop two experimental indexes on a stopped deterministic dataset. Source delivery_004 migrations stay unchanged; final source metadata comparison passes. Ordinary fixture CREATE INDEX is not a concurrent production index rollout or workload/load/backup proof. Keep planner statistics, warm caches, write/storage cost and LIMIT effects beside the saved observations. The API never executes the SQL lab; full academy operations remain open.


## Local API-depth operating limit

Five ordered lessons (python-http-validators through python-api-depth-evidence), ten original scenarios under separate API delivery contracts and complete guided/diagram/glossary/private recall layers connect to the API depth lab. Its authenticated fourteen-file starter has three unfinished functions, 51 public cases (39 offline/12 PostgreSQL) and four manual criteria. Nine freshly installed packages verify private conditional GET/permission ordering, framed raw-byte HMAC/freshness/strict events, atomic scoped receipts/readings, real competing duplicates/conflicts/rollback/lock timeout and compatible prior routes. The saved actual loopback HTTP report observes 200/304/change, 401/403/409/422/503/retry, committed counts and released connections. Reported tests and manual review do not award mastery (ADR 0034).

This is a local installed HTTP/store exercise. Its explicit fixture table is not a production schema migration/retention or key rotation system. Imports/factories/requests have no DDL. Readiness observes source head/columns and receipt shape; it does not guarantee subsequent admission or inspect every constraint/data row. Individual SQL limits do not impose a hard whole-request deadline. Public TLS/proxies/hostile clients and external-effect exactly-once guarantees remain open; full academy Compose/isolated restore is verified separately in ADR 0042. Original release runbook and rollback/history-loss limits remain in ADR 0032.


## Composed advanced Python practical review

Five lessons (`python-practical-contracts` through `python-practical-review`), ten original scenarios and complete guided/diagram/glossary/private recall layers connect to the Composed Python practical review lab. Its authenticated eighteen-file starter has three unfinished functions, 50 public cases (47 offline/three PostgreSQL) and four manual criteria covering all seven advanced review dimensions. Eight freshly installed local packages compose strict old service pages, latest/conflict/domain adapters, immutable typed snapshots, response/resource ownership, bounded cache and actual thread/spawn workers. A stated 128-fact workload gives equivalent reporting outputs with 152/32 computations and 120 hits; a cyclic case gives 64/64 and zero hits. Actual cProfile call counts, raw wall/CPU intervals and Python allocation observations have no speed threshold. The original-case/regression/design task feeds fixed manual submissions and revisions. Maintainer fixtures and reported tests never establish learner originality, mastery or expertise (ADR 0035).

This is a stopped-fixture local practical review, not public service/academy operations. It creates an isolated original service_002 schema; later delivery_004 rehearsals remain unchanged. Four HTTP pages are collected after writers stop, without a global read-snapshot promise. Profiling starts after collection and is not end-to-end throughput, process RSS, deployment capacity or production evidence. Academy Compose/isolated backup restore is verified in ADR 0042; public operations remain open.


## Offline model contracts

Six lessons (`model-request-contracts` through `model-contract-evidence`), twelve original scenarios under separate **Model call contracts** and complete guided/diagram/glossary/private recall layers connect to the Model contracts lab. Its authenticated fourteen-file starter has three unfinished functions, **84 offline public cases** and four manual criteria. A clean installed standard-library package normalizes two invented provider formats; checks pinned model/prompt/schema, copied complete-envelope context/output admission, strict complete/refused/incomplete proposal/usage variants; and reserves fictional credits before attempts, settles only valid usage, retains unknown reserves and stops at cost/step/one cooperative deadline boundaries. Actual waiting fixtures verify timeout cleanup and propagated external cancellation. Installed JSON records eleven finite cases without raw prompts/refusal reasons/exceptions. No real model, network, current pricing, provider conformance or semantic quality is claimed (ADR 0036).

This is an offline application-contract rehearsal. No provider integration, tokenizer conformance, real pricing, durable distributed quotas, retries/reconciliation or public model-serving operation is deployed. A single monotonic deadline covers cooperating provider waits after preflight; it does not promise hard elapsed-time interruption. Real provider/model/schema capability versions, privacy/retention, billing and failure behavior require independent deployment evidence. Academy Compose and isolated backup restore are verified in ADR 0042; public operation remains open.


## Scoped retrieval contracts

Six lessons (`retrieval-chunk-identities` through `retrieval-evidence`), twelve original scenarios under separate **Scoped retrieval contracts** and complete guided/diagram/glossary/private recall layers connect to the Scoped retrieval lab. Its authenticated fifteen-file starter has three unfinished functions, **83 public cases** and four manual criteria. The installed standard-library package preserves complete chunk keys/character offsets/digests, validates model/version/dimensions/finite nonzero vectors, chooses latest revisions before trusted tenant/group/activity/metadata filters, then computes exact cosine or simple ASCII token-set Jaccard ranking with full-key ties. Requested-k precision, labelled recall and first-relevant rank use explicit denominators; no-label cases have null recall/rank and separate unwanted-hit counts. Four computed reports use an original 12-revision/15-chunk/nine-query development fixture with hand-supplied six-dimensional vectors. No real embedding model, ANN/database index, held-out quality, durable document lifecycle or automatic mastery is claimed (ADR 0037).

This finite in-memory lab deploys no embedding provider or pgvector index. Production model revisions, corpus/ACL synchronization, update/delete lifecycle, ANN recall, realistic load and held-out quality need separate deployment evidence. The bounded scan is not a hard resource-isolation guarantee. Academy Compose and isolated backup restore are verified in ADR 0042; public operation remains open.


## RAG continuation (2026-10-11)

The RAG index is an explicitly separate, finite local SQLite exercise, not the academy database or a PostgreSQL deployment design. No academy migration/runtime dependency is added. The lab uses controlled generation and hand vectors; source digests, tombstones and epoch checks are local observations, not distributed corpus freshness or production authority. PostgreSQL deployment, real provider tokenization/billing, backup/retention, durable call reconciliation and semantic release evaluation remain separate work. Do not deploy the maintained fixture provider as a real answer service.


## Tool-use continuation (2026-10-11)

Authorized tool practice uses a separate finite local SQLite note/receipt store and controlled providers. No academy migration/runtime dependency is added. Local atomic note/receipt replay is not a production PostgreSQL or remote exactly-once design. Current application metadata/callbacks, approval digests and cooperative deadlines are explicit assumptions, not deployed authentication, cryptographic grants, hard isolation or durable billing. Real side effects need their own idempotency/approval/reconciliation and release evidence; do not deploy these fixtures as a production agent.


## Final step-six evaluation (2026-10-12)

Controlled release evaluation composes five local packages with temporary SQLite fixtures and controlled providers. It adds no academy migration/runtime dependency. A fixture objective pass with pending semantic review is not production release approval. No held-out real-model/security/reviewer authentication is claimed. Local note receipts, trusted authority, byte cost units and cooperative waits retain their earlier limits; academy PostgreSQL/Compose, isolated backup/restore and offline account recovery are verified in ADR 0042; broader real public release operations remain future work.
