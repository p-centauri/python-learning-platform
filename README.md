# Forge — Backend & AI Engineering Academy

Formerly "Form — Engineering Academy" (renamed 2026-10-29, [ADR 0046](docs/adr/0046-product-name-forge.md)). Hosted at **https://eng.xosilov.com**.

A personal learning application for an experienced developer building Backend + Applied AI engineering competence. Learn the mental model, practice failure scenarios, and track evidence rather than page views.

**Current release: a working academy with bounded teaching and practical labs.** It includes 195 authored lessons, 390 distinct objective exercises, a 10-question diagnostic pilot, and separate beginner (20 questions), intermediate (24 questions) and advanced (28 questions) Python evaluations. Six Python/PostgreSQL coding exercises with 25 isolated checks are also available. Three comprehensive exams now add 48 mixed knowledge questions, a 23-case isolated application repair and a staged senior design case. Three complete portfolio build packs connect requirements, failure evidence and invited review. Learners build the products themselves; finite checks/manual review do not certify expertise. Offline account recovery, session/password controls and private evidence downloads now support everyday study. Broader expert curriculum and public production acceptance remain tracked explicitly.

## Hosted academy

Open **[the hosted academy](https://eng.xosilov.com)** and create your account. This installation starts fresh; your original local history is preserved separately. It uses trusted HTTPS and its own PostgreSQL storage alongside the existing carwash app. Hosted coding/SQL/practical-repair execution is unavailable until a separate isolated worker is deployed; draft saving and local starter downloads remain available. See [server operations and verified scope](docs/SERVER_DEPLOYMENT.md).

## Run locally

With Docker Desktop running:

```sh
docker compose up --build
```

Open [the academy](http://localhost:3000) and create your own account. No shared demo password or API key is required. PostgreSQL data persists in the `academy_data` volume. **Full Compose/PostgreSQL startup, real business persistence/restart and isolated backup restore are verified.** Use unique private credentials and read [the operating guide](docs/OPERATIONS.md) before starting a new deployment. SQLite study history is preserved separately; Compose does not import it.

Without Docker (Python 3.13+, Node 22+):

```sh
make setup
make dev
```

This runs the same application using a local SQLite file for learning state. Visit [the local workspace](http://127.0.0.1:3000). SQLite is a local convenience, not proof of PostgreSQL concurrency behavior. See [DEVELOPMENT.md](DEVELOPMENT.md) for commands and ports.

## What works

- Account registration/sign-in, offline one-use recovery at `/recover`, password changes and owned session revocation at `/account`. No recovery email is invented.
- Private JSON/Markdown downloads of saved learning evidence at `/account`, excluding credentials and active private keys; exports are not database imports.
- Personal learning plans: choose a goal and weekly hours, get an explained starting point and an adaptive study queue at `/plan`.
- Responsive dashboard, full 23-track curriculum map and 195 real lesson pages.
- Lesson completion, persistent personal notes and bookmarks.
- Every published lesson has prediction/debugging checkpoints, saved simple feedback, a text-accessible diagram, section links and track navigation. A searchable 390-term glossary links back to teaching. Guided work is separate from reading, mastery and delayed recall.
- Coding and SQL lab: three Python and three PostgreSQL contracts, saved drafts, real isolated test feedback and fixed history. See [runner setup](DEVELOPMENT.md#isolated-coding-runner) to enable execution.
- Scenario exercises with progressive hints, server-side grading, attempt history and gated explanations.
- Evidence-based skill scores, weak areas, recommendations and due review scheduling.
- Mistake-driven review at `/review`: 390 short-answer variations across 195 topics, saved checks, simple feedback, delayed scheduling and separate recognition/retention evidence. Due checks appear in the personal plan; viewed repeats and reported help receive separate labels.
- A resumable diagnostic with hidden answers until submission and category analysis afterward.
- Separate beginner/intermediate/advanced Python tests with saved answers, topic feedback, stable attempt snapshots and [level-specific library guides](docs/PYTHON_LEVELS.md).
- Eight lessons on coroutines, task groups, cancellation, total deadlines, bounded queues and async HTTP ownership, with an installable lab and 75 offline pytest cases.
- Seven lessons on closures, binding, decorators, pytest design, safe logging and bounded regex, with a separate filtering/reporting starter and 49 offline pytest cases.
- An eight-lesson packaging/HTTP ingestion module with 16 scenarios and an installable lab: 28 offline public tests, strict types/lint, real source-archive/wheel builds and clean-installed commands/resources.
- A five-lesson generators/resource-cleanup module with ten scenarios and a streaming service-log lab with 16 local tests for laziness, bounded reads and reliable cleanup.
- A five-lesson object-design module with ten scenarios and a typed task-inbox project: classes, dataclasses, composition, hints and protocols. Runtime tests and mypy provide separate evidence.
- A five-lesson continuation on text, collection patterns, dates/time and debugging, with ten scored scenarios and an event-timeline repair lab with 13 local tests.
- A nine-lesson Python foundations module with 18 scored scenarios, plus an expense-tracker CLI starter, sample data and 13 local acceptance tests.
- Thirty-five workspaces: twenty-nine local starters, three portfolio build products and three exam review workspaces. Reading and manual checklists do not certify practical skill.
- Project submissions, pinned rubrics, self-review, invited-account human feedback and revision history. Saved artifacts include a repository reference and reported local test evidence; the academy does not execute submitted code.
- Search across lesson text, exercises, project briefs and personal notes; Cmd/Ctrl+K.
- Light/dark themes, mobile navigation, keyboard focus, semantic controls and safe Markdown rendering.

## Continue development in another session

The root [AGENTS.md](AGENTS.md) instructs future agents to read and maintain:

1. [docs/STATUS.md](docs/STATUS.md) — verified state, limitations and exact next action.
2. [docs/ROADMAP.md](docs/ROADMAP.md) — milestones and unfinished requirements.
3. [docs/PROGRESS.md](docs/PROGRESS.md) — append-only implementation and test history.

The full original request is preserved in [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md). Architecture decisions live in [docs/adr](docs/adr).

## Technical documentation

[Python learning path and missing lessons](docs/PYTHON_LEARNING_PATH.md) · [Python libraries by level](docs/PYTHON_LEVELS.md)

[Architecture](ARCHITECTURE.md) · [Curriculum](CURRICULUM.md) · [Assessment model](ASSESSMENT_MODEL.md) · [Database](DATABASE.md) · [Security](SECURITY.md) · [Deployment](DEPLOYMENT.md) · [Everyday operations/recovery](docs/OPERATIONS.md) · [Contributing](CONTRIBUTING.md)

The advanced object-behavior unit adds six lessons from `/lessons/python-attribute-lookup`, 12 original scenarios and a separately installable feed-object lab with 50 public cases. It covers descriptor ownership, cooperative MRO traces, implicit special methods and immutable equality/hash contracts. Advanced typing and context/resource lifetime are published separately. Threads/processes and measured performance are published separately; all nine fixed step-six milestones are verified.

Seven advanced typing lessons start at `/lessons/python-generic-functions`: generic relationships, variance, ParamSpec wrappers, overloads, narrowing, validated unknown input and typed library interfaces. The installable transformation lab supplies 47 runtime cases plus one positive/ten rejected checker fixtures, with clean installed record/snapshot composition and four manual criteria. Neither reported tests nor annotations certify expertise. Context/resource lifetime is published next within step 6.

Six context/resource lessons start at /lessons/python-exit-stack. They teach partial acquisition, cleanup errors, awaited release, ContextVars and weak-reference lifetime. An eight-file standard-library starter supplies 54 public cases, installed composition and four manual criteria. Thread/process concurrency is published next in the sequence; the fixed step-six scope is now verified.

Seven thread/process lessons start at /lessons/python-thread-process. They cover shared invariants/locks, future cancellation versus waiting, bounded admission, explicit spawn/serialization, worker-owned resources and build/runtime GIL reporting. The nine-file standard-library bounded offload starter has three unfinished functions and 66 public cases, real installed process execution and four manual criteria. Measured profiling/cache/library evolution is published separately; no speedup or expertise is claimed.

Eight measurement/cache/compatibility lessons start at /lessons/python-measurement-baselines. A ten-file standard-library starter has four unfinished functions/methods and 61 public cases, actual wall/CPU/profile/allocation observations, clean installed six-package composition and four manual criteria. Correctness checks avoid machine-specific speed thresholds. The first PostgreSQL persistence unit is published separately; the fixed step-six scope is now verified.

Eight PostgreSQL persistence lessons start at /lessons/python-relational-keys. An eleven-file installable starter has three unfinished functions, 57 public cases and four manual criteria. The installed reference uses real PostgreSQL constraints, parameter binding, committed duplicate counts, late whole-batch rollback, bounded ordered reads and typed earlier-package integration. Missing database configuration explicitly skips database cases. FastAPI/SQLAlchemy/Alembic service integration is published next in the sequence; the fixed step-six scope is now verified.

Eight ingestion-service lessons start at `/lessons/python-http-api-contracts`. They teach strict Pydantic input, permission checks, SQLAlchemy session/transaction ownership, Alembic schema evolution, scoped pagination and safe failure evidence. The nineteen-file installable starter supplies three unfinished functions, 70 public cases and four manual criteria. The installed reference passes all cases on real PostgreSQL, migration rehearsals, prior-package composition and a real loopback HTTP server check. Missing database configuration labels 27 cases as skipped. A bounded competing-transaction/lock/retry/reconciliation unit is published separately; the first outbox/worker/process-replay unit is delivered in ADR 0027; the bounded leases/backoff/shutdown continuation is delivered in ADR 0028; the whole learning path remains unfinished.

Seven lessons start at `/lessons/python-pg-snapshots` and connect the prior ingestion API to real PostgreSQL competition. The thirteen-file extension starter has three unfinished functions, 70 public cases and four manual criteria. Installed evidence observes waits, commit/rollback races, snapshot differences, 40001/40P01/55P03/57014, fresh whole-transaction attempts and read-only fact reconciliation. A modeled missing response after real commit is labeled separately. Complete the prior service wheel before installing this local extension. The academy never executes it or awards mastery from its reported results (ADR 0026).

Six lessons start at `/lessons/python-outbox-atomicity`. The fourteen-file durable-outbox starter extends the completed service/competition wheels with three unfinished functions and 67 public cases. Installed PostgreSQL evidence verifies fact/intent and inbox/effect transactions, stable keys, separate locked claims and real subprocess exits before producer commit, after producer commit and after consumer commit before acknowledgment. Restart preserves one local database application. This sink is PostgreSQL, not a broker; worker recovery is distinct from database power-loss recovery. Four manual criteria preserve evidence and limits (ADR 0027).

Six leased-worker lessons start at `/lessons/python-worker-leases`. Six ordered lessons (python-worker-leases through python-worker-evidence) add twelve original scenarios under Worker lease contracts, twelve guided choices/terms/private recall variants and six diagrams. The authenticated fourteen-file leased-worker extension has three unfinished functions and 59 public cases (35 offline/24 PostgreSQL-dependent), with four manual review criteria. Four freshly built/installed local packages on PostgreSQL 17.11 verify short committed leases, copied stable events, current-generation/live-deadline settlement, persisted retry times/attempt limits, poison/exhaustion quarantine, bounded admission, real acknowledgment rollback, two actual child exits/observed expiry/generation-2 reclaims and cooperative SIGTERM. Replay preserves one local consumer effect. Old Event/Accepted/service routes and permissions remain unchanged; reported output and checklists do not award mastery (ADR 0028). The fixed step-six scope is now verified.

Six broker/event-evolution lessons start at `/lessons/python-event-envelopes`. Six ordered lessons (python-event-envelopes through python-stream-evidence), twelve original scenarios under separate Stream delivery contracts, and complete guided/diagram/glossary/private recall layers connect to the Broker delivery lab. Its authenticated fifteen-file starter has three unfinished functions, 74 public cases (59 offline/15 live) and four manual criteria. Five fresh installed local packages verify strict supported v1/v2 envelopes with stable Event identity, checked Redis XADD/WAITAOF local AOF acceptance on one physical connection, producer completion before consumer effects, inbox/effect commit before XACK, pending/reclaim/cursor/deleted-gap semantics, duplicate/conflicting facts, real constraints, two actual child exits and a controlled retained-AOF broker restart. PostgreSQL 17.11, Redis 7.4.2 and redis-py 6.4.0 are observed; reported evidence does not award mastery (ADR 0029). The fixed step-six scope is now verified.


## Delivery migration rehearsal

Six ordered lessons (python-delivery-revisions through python-migration-evidence), twelve original scenarios under separate Delivery migration contracts, and complete guided/diagram/glossary/private recall layers connect to the Delivery migration lab. Its authenticated sixteen-file starter has three unfinished functions, 44 public cases (25 offline/19 live) and four manual criteria. Six freshly built/installed packages on PostgreSQL 17.11 verify an unchanged service_001/002 plus delivery_003/004 chain, all-field/timestamp preservation without implicit enqueue, combined metadata/head/autogenerate comparison, actual late upgrade/downgrade rollback, cooperating advisory locks/real DDL timeout, explicit destructive targets and retained facts versus lost delivery history. Actual Redis composition preserves prior contracts; old service /ready intentionally reports 503 at the new head. Re-upgrade has empty inbox history and can apply the same key again. Finite reported evidence does not award mastery (ADR 0030).

Use `make verify-delivery-schema` for the trusted installed artifact/store verifier. The fixed step-six scope is now verified; bounded retention/redrive is delivered in ADR 0031 and bounded release compatibility is delivered in ADR 0032; bounded SQL query depth/plans are delivered in ADR 0033; API depth is delivered in ADR 0034; advanced practical review is delivered in ADR 0035; model contracts are delivered in ADR 0036; embeddings and retrieval are delivered in ADR 0037; RAG is delivered in ADR 0038; tool use is delivered in ADR 0039; AI evaluation/security and final audit are delivered in ADR 0040; fixed step six is complete.


## Delivery retention and explicit redrive

Four ordered lessons (python-dead-job-inspection through python-recovery-evidence), eight original scenarios under separate Delivery recovery contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery recovery lab. Its authenticated twelve-file starter has three unfinished functions, 36 public cases (14 offline/22 live) and four manual criteria. Seven installed packages on owned PostgreSQL/Redis verify bounded inspection, one concurrent redrive success, preserved Event/generation/policy, exhausted refusal, stale-lease refusal, local rollback, atomic current-group payload checks and duplicate-safe replay with all local history retained. Payload deletion can survive later call failure. Reported evidence does not award mastery (ADR 0031).


## Compatible local releases

Four ordered lessons (python-release-settings through python-release-evidence), eight original scenarios under Release operating contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery release lab. Its authenticated fourteen-file starter has three unfinished functions, 33 public cases (15 offline/18 live) and four manual criteria. Eight installed packages on owned PostgreSQL/Redis verify private copied settings, compatible delivery_004 readiness, preserved business contracts, real failures, one owned disposal, installed operating commands/loopback SIGTERM cleanup and exact rollback losses with re-upgrade. Reported evidence does not award mastery (ADR 0032).

Start at `/lessons/python-release-settings`. Use `make verify-delivery-release` for trusted installed evidence; the downloaded RUNBOOK.md describes private configuration, explicit prepare/check/serve/rollback, stopped writers and retained/lost history. Full academy deployment and step 6 remain open.


## SQL query analysis

Five ordered lessons (python-query-joins through python-query-evidence), ten original scenarios under SQL query analysis contracts and complete guided/diagram/glossary/private recall layers connect to the SQL query analysis lab. Its authenticated nineteen-file starter has three unfinished SQL queries, 36 public cases (23 offline/13 PostgreSQL) and four manual criteria. Nine installed packages verify complete-key/fanout/empty reports, zero-safe revision windows, newest-before-JSONB filtering, read-only owned queries, source compatibility and actual result-equivalent baseline/indexed plans on 40,000 records/notes. Five literal lesson SQL examples also run on PostgreSQL. Reported evidence does not award mastery (ADR 0033).

Start at `/lessons/python-query-joins`. Use `make verify-query-analysis` for the trusted installation/store verifier. Baseline/indexed plans preserve ordered results and record estimates/rows/loops/root buffers/cost/time; no fixed plan or timing threshold is a passing gate. The fixed step-six scope is now verified; API depth is delivered in ADR 0034; advanced practical review is delivered in ADR 0035; model contracts are delivered in ADR 0036; embeddings and retrieval are delivered in ADR 0037; RAG is delivered in ADR 0038; tool use is delivered in ADR 0039; AI evaluation/security and final audit are delivered in ADR 0040; fixed step six is complete.


## API depth

Five ordered lessons (python-http-validators through python-api-depth-evidence), ten original scenarios under separate API delivery contracts and complete guided/diagram/glossary/private recall layers connect to the API depth lab. Its authenticated fourteen-file starter has three unfinished functions, 51 public cases (39 offline/12 PostgreSQL) and four manual criteria. Nine freshly installed packages verify private conditional GET/permission ordering, framed raw-byte HMAC/freshness/strict events, atomic scoped receipts/readings, real competing duplicates/conflicts/rollback/lock timeout and compatible prior routes. The saved actual loopback HTTP report observes 200/304/change, 401/403/409/422/503/retry, committed counts and released connections. Reported tests and manual review do not award mastery (ADR 0034).

Start at `/lessons/python-http-validators`. Use `make verify-api-depth` for the trusted installed artifact/store/HTTP verifier. The lab uses its own signed protocol, explicit disposable DDL and a borrowed engine; public deployment/key rotation/external exactly-once effects remain open. All eight agreed learning-experience steps are complete within their recorded academy/local acceptance scopes (ADRs 0041–0042). Broader expert curriculum, independently reviewed learner portfolio work and public production acceptance remain in ROADMAP. Wait for the user to continue before starting another bounded milestone; do not infer expertise or public readiness from finite checks/checklists.


## Composed advanced Python practical review

Five lessons (`python-practical-contracts` through `python-practical-review`), ten original scenarios and complete guided/diagram/glossary/private recall layers connect to the Composed Python practical review lab. Its authenticated eighteen-file starter has three unfinished functions, 50 public cases (47 offline/three PostgreSQL) and four manual criteria covering all seven advanced review dimensions. Eight freshly installed local packages compose strict old service pages, latest/conflict/domain adapters, immutable typed snapshots, response/resource ownership, bounded cache and actual thread/spawn workers. A stated 128-fact workload gives equivalent reporting outputs with 152/32 computations and 120 hits; a cyclic case gives 64/64 and zero hits. Actual cProfile call counts, raw wall/CPU intervals and Python allocation observations have no speed threshold. The original-case/regression/design task feeds fixed manual submissions and revisions. Maintainer fixtures and reported tests never establish learner originality, mastery or expertise (ADR 0035).

Start at `/lessons/python-practical-contracts` and use `make verify-practical-review`. Submit your own case, regression, versioned report and explanation through the linked project. The supported eight-package service_002 composition keeps later delivery/query/API histories unchanged.


## Offline model contracts

Six lessons (`model-request-contracts` through `model-contract-evidence`), twelve original scenarios under separate **Model call contracts** and complete guided/diagram/glossary/private recall layers connect to the Model contracts lab. Its authenticated fourteen-file starter has three unfinished functions, **84 offline public cases** and four manual criteria. A clean installed standard-library package normalizes two invented provider formats; checks pinned model/prompt/schema, copied complete-envelope context/output admission, strict complete/refused/incomplete proposal/usage variants; and reserves fictional credits before attempts, settles only valid usage, retains unknown reserves and stops at cost/step/one cooperative deadline boundaries. Actual waiting fixtures verify timeout cleanup and propagated external cancellation. Installed JSON records eleven finite cases without raw prompts/refusal reasons/exceptions. No real model, network, current pricing, provider conformance or semantic quality is claimed (ADR 0036).

Start at `/lessons/model-request-contracts` after the LLM introduction and Python practical review; use `make verify-model-contracts`. No provider account/API key is needed. Build/install the completed package outside source, save the report and submit an independent regression/design note through the linked manual project.


## Scoped embeddings and retrieval

Six lessons (`retrieval-chunk-identities` through `retrieval-evidence`), twelve original scenarios under separate **Scoped retrieval contracts** and complete guided/diagram/glossary/private recall layers connect to the Scoped retrieval lab. Its authenticated fifteen-file starter has three unfinished functions, **83 public cases** and four manual criteria. The installed standard-library package preserves complete chunk keys/character offsets/digests, validates model/version/dimensions/finite nonzero vectors, chooses latest revisions before trusted tenant/group/activity/metadata filters, then computes exact cosine or simple ASCII token-set Jaccard ranking with full-key ties. Requested-k precision, labelled recall and first-relevant rank use explicit denominators; no-label cases have null recall/rank and separate unwanted-hit counts. Four computed reports use an original 12-revision/15-chunk/nine-query development fixture with hand-supplied six-dimensional vectors. No real embedding model, ANN/database index, held-out quality, durable document lifecycle or automatic mastery is claimed (ADR 0037).

Start at `/lessons/retrieval-chunk-identities` after the similarity and model-contract introductions. Use `make verify-retrieval`; no provider account, model download or Docker is needed for this verifier. Build/install outside source, save retrieval.json and submit an independently predicted regression/decision note for manual review.


## Verified RAG continuation (2026-10-11)

Six simple lessons (`rag-source-lifecycle` through `rag-practical-evidence`), twelve original scenarios under separate **Evidence answering contracts** and complete guided/diagram/glossary/private recall layers connect to the Evidence answering lab. Its authenticated fifteen-file starter has three unfinished functions, **70 public cases** and four manual criteria. The installed `academy-rag-lab==0.1.0` composes the published model and retrieval packages. A separate local SQLite index atomically publishes complete revisions, retains deletion markers and rejects older/conflicting publication. Trusted access filters, a stated task-term gate, keyword reranking and whole-passage UTF-8 packing select evidence before a bounded controlled call. Exact selected excerpts become citations only after current permissions, source identity and index epoch are rechecked. Missing evidence, invalid output and stale authority return no answer text. Seventeen computed experiments observe lifecycle, refusal, invalid proposals, admission, cancellation and freshness. Controlled quotes and hand-assigned vectors do not evaluate semantic answer quality or production authorization; manual submissions never award mastery (ADR 0038).

All eight agreed learning-experience steps are complete within their recorded academy/local acceptance scopes (ADRs 0041–0042). Broader expert curriculum, independently reviewed learner portfolio work and public production acceptance remain in ROADMAP. Wait for the user to continue before starting another bounded milestone; do not infer expertise or public readiness from finite checks/checklists.


## Verified tool-use continuation (2026-10-11)

Six simple lessons (`tools-proposal-boundaries` through `tools-practical-evidence`), twelve original scenarios under separate **Authorized tool contracts** and complete guided/diagram/glossary/private recall layers connect to the Authorized local tools lab. Its authenticated fifteen-file starter has three unfinished functions, **81 public cases** and four manual criteria. The installed `academy-tools-lab==0.1.0` composes model, retrieval and RAG packages. Strict proposals cannot grant authority; current application actor/principal/source checks and exact action approval precede effects. One local transaction commits a note and its scoped receipt under a stable application operation ID independent of model call IDs. Same actions replay, changed actions conflict, caps and late SQL failures are observed. One cooperative whole-loop deadline and context/cost/step budgets stop uncertain outcomes without automatic effect retries. Seventeen computed experiments observe actual calls, notes/receipts, lost-result reconciliation and cancellation; public reports redact source text and pin provider/model/prompt/schema. Controlled local evidence is not real model quality, production authority or distributed exactly-once; manual submissions never award mastery (ADR 0039).

All eight agreed learning-experience steps are complete within their recorded academy/local acceptance scopes (ADRs 0041–0042). Broader expert curriculum, independently reviewed learner portfolio work and public production acceptance remain in ROADMAP. Wait for the user to continue before starting another bounded milestone; do not infer expertise or public readiness from finite checks/checklists.


## Verified final step-six evaluation and path audit (2026-10-12)

Six simple lessons (`ai-release-cases` through `ai-release-review`), twelve original scenarios under separate **AI release evidence** and complete guided/diagram/glossary/private recall layers connect to the Controlled AI release evaluation lab. Its authenticated fifteen-file starter has three unfinished functions, **54 public cases** and four manual criteria. Five installed packages execute eighteen versioned development cases for each of two candidates: **36 actual observations**. Requested-k precision is **1/4** and positive-label recall/MRR **1/2**; raw cosine has **one** unlabelled unwanted hit and the stated task-term gate has **zero**. Exact answer/tool contracts, permission/privacy/boundary counts, dataset/candidate digests and inclusive rational thresholds remain separate from two pending semantic reviews. Reports redact raw contents; role/URL/extra-field, stale-source and post-commit timeout paths are observed. The separately labelled mutation demonstrates evaluator rejection rather than claiming another provider run. Controlled development data and hand vectors do not establish real model quality or production security (ADR 0040).

The agreed nine-milestone teaching/lab sequence is complete. [Coverage audit](docs/COVERAGE_AUDIT.md) records the actual boundaries; broader product/portfolio/reliability work remains planned.

All eight agreed learning-experience steps are complete within their recorded academy/local acceptance scopes (ADRs 0041–0042). Broader expert curriculum, independently reviewed learner portfolio work and public production acceptance remain in ROADMAP. Wait for the user to continue before starting another bounded milestone; do not infer expertise or public readiness from finite checks/checklists.
