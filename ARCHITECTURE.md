# Architecture

## Product shape
A personal engineering academy with multiple isolated learner accounts. Curriculum is authored and versioned in Git; learner state belongs in the database. The first delivery is an independently usable slice, followed by deeper content and practical execution infrastructure.

## Runtime
Browser → Next.js App Router → same-origin `/api` proxy → FastAPI modular monolith → PostgreSQL.

Next.js owns presentation, navigation and transient form state. FastAPI owns authentication, validation, answer secrecy, grading and all progress mutations. SQLAlchemy uses one transaction-scoped session per request. Alembic owns schema creation. SQLite is an explicit local/test convenience; it does not establish PostgreSQL concurrency correctness.

## Folder structure
```
apps/api/app/        settings, database, models, auth, domain services, API routers
apps/api/alembic/    versioned schema migrations
apps/api/tests/      behavioral API/domain tests
apps/runner/runner/ trusted private Docker controller; learner execution only in containers
apps/web/src/       App Router, feature components, primitives, API types
content/            versioned metadata, Markdown lessons, server-only answer keys
docs/adr/           engineering decisions
docs/               status, roadmap, append-only progress, original brief
```

## Boundaries
Curriculum definitions are read-only application inputs. Seeded records make stable IDs and foreign keys possible. Learning services own attempts and review scheduling; assessment services own exam lifecycle. Passwords use a memory-hard password hash. Opaque sessions are stored hashed server-side and transported by HttpOnly cookies. Same-origin requests plus an explicit custom request header and Origin validation protect mutations.

## UI information architecture
- Personal plan: saved learning goal and weekly budget, explained entry point, rolling study queue, submitted assessment evidence and published route.
- Overview: personal next action or setup prompt, continue lesson, real evidence totals, skills, review due, next action.
- Learning path: ordered tracks/modules, published vs planned content.
- Lesson: Markdown reading, objectives, section links, track navigation, diagrams, guided prediction/debugging checkpoints, local glossary, notes/bookmark and scenario practice.
- Practice: scenarios, options, progressive hints, submission feedback and attempts.
- Coding and SQL: six contracts, plain-text editor, saved drafts, isolated execution feedback and fixed run history.
- Review/progress: recurring mistake signals, immediate and delayed short-answer checks, saved drafts, fixed history and recognition/retention evidence shown separately; the original scenario queue remains available.
- Projects: twenty-nine local Python starters and three portfolio briefs with persistent milestones, saved submission drafts, fixed artifact versions, pinned project rubrics and revision history. Owners record self-review and invite registered accounts for human feedback. The review workspace lists only explicitly invited versions; local tests remain learner-reported. Packaging/HTTP practice uses a separately tested installable local lab, never API execution (ADR 0016).
- Assessments: original pilot/Python levels plus mixed knowledge, isolated practical repair and staged design with fixed evidence and invited review (ADR 0041).
- Library: searchable lessons, bookmarks and a linked glossary. Cmd/Ctrl+K opens global search, including glossary terms.

Only working areas receive navigation. Avoid decorative controls or simulated statistics.

## Project review boundary
The projects router owns submission versions, reviewer grants and feedback. Owner operations remain learner-scoped; an active invitation permits a reviewer to see only the selected submitted artifact, rubric and feedback. Feedback identity and self/human classification come from the authenticated account. New revisions pin the current authored rubric and retain a parent reference; old artifacts and feedback stay fixed. Repository links are stored without fetching their contents. No submitted code or test command is executed. See ADR 0012.

## Extension points
The coding router calls a separate authenticated loopback runner. Its fixed Docker profile is verified at startup; execution happens in fresh containers and results stay separate from mastery. The API never executes learner source or controls Docker. See ADR 0013 for limits and the local release boundary. Introduce Redis/queues only for measured needs (distributed throttling, ingestion, grading jobs). An LLM is not required to grade objective questions and is not a trusted authority for practical competence.

## Recall boundary
The retention router derives topic mistakes/schedules from account-owned scenario attempts and recall sessions. The server pins private definitions and grades exact short answers without execution. Original recognition, immediate practice, unseen delayed questions, repeated questions and assisted work have separate evidence counts. Dashboard and personal-plan recommendations expose due checks without awarding mastery. Content lives in `content/review-questions.json`; all 195 published lesson topics have two finite variations. See ADR 0014 for seen-question tracking, help reporting and provisional scheduling.

## Guided lesson boundary
The interactivity router owns immutable guided attempts. Native figures/lists and authored JSON keep teaching outside React. Keys stay private until submission; fixed feedback survives content edits. Recorded checkpoints are study exposure for recall scheduling but remain separate from mastery/retention results. See ADR 0015.

## References
- [Next.js documentation](https://nextjs.org/docs)
- [FastAPI authentication documentation](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [SQLAlchemy session lifecycle](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)

## Policy extension lab

The function/testing unit is authored content plus a separately installable standard-library package. Its read-only protocol accepts previous ingestion records without changing the HTTP/parser contract. Local acquisition remains owned by the earlier context; reporting borrows a lazy filtered input. The API serves a fixed nine-file starter and stores manual review evidence; it does not execute the package. Trusted reference installation/composition checks run in maintainer subprocesses (ADR 0017).

## Async local lab

The async unit is a separately installed HTTPX package with a fixed worker pool, bounded queue and TaskGroup lifetime. It returns complete in-memory aggregates after owned responses/generators close, with cooperative cancellation/deadlines. A typed async opener reuses the previous selector without changing either synchronous package. This is local teaching, not a database worker or API execution path. Maintainer subprocesses check trusted reference artifacts and offline composition; learner evidence remains manual (ADR 0018).

## Local object-contract lab

The advanced object unit is authored content and an independently installed standard-library package. Shared data descriptors store each Budget field on its owner; frozen FeedKey values use the same stable fields for equality and hashing. Snapshot copies at most 64 distinct readings in order from a borrowed iterable, observing one extra item to establish overflow. A typed offline adapter accepts prior installed ingestion records without changing either contract. The authenticated seven-file starter excludes references and keys. The API stores manual evidence and serves bytes only; trusted maintainer subprocesses verify artifacts (ADR 0019).

## Local typed transformation lab

The typing unit is authored content plus a separately installed standard-library package. Generic mapping preserves input/mapper/result relationships while bounding observed work; ParamSpec wrappers preserve call shapes and explicit call-return/error phases. Overloads describe optional/default results, while an honest structural guard and domain constructor validate actual current input. The eleven-file authenticated starter includes public runtime and checker fixtures. Trusted maintainer subprocesses run 47 runtime cases and inspect positive/ten negative fixtures without executing those snippets. A strict-typed installed adapter uses prior Records and Snapshots without changing their contracts. The API serves bytes and stores manual evidence only (ADR 0020).

## Local resource-scope lab

Factories own partial acquisition until returning a cleanup handoff. Bounded scopes immediately register successful callbacks, unwind in reverse order and await asynchronous release. A ContextVar token restores request metadata; weak lookup does not own lifetime. The eight-file authenticated starter excludes references and keys. Trusted maintainer subprocesses check 54 cases, source/wheel artifacts and typed installed composition with prior values. The API serves bytes and stores manual evidence only (ADR 0021).

## Local bounded offload lab

The nine-file allowlist for bounded-offload serves authored starter bytes only. collect_ordered borrows an executor/input and coordinates a finite submitted-but-not-retired window. run_batch owns a dedicated thread or explicit spawn process pool through wait/cancel-queued shutdown. Workers acquire/close their own file handles; the caller retains named files until shutdown. Only trusted reference subprocesses build/install/run this package and prior-value adapters. The academy API never imports or executes learner packages. Manual evidence remains separate from objective isolated grading. No persistence, recovery, hard interruption or speedup is claimed (ADR 0022).

## Local measured-cache lab

The ten-file authored starter separates raw finite sample collection, single-caller LRU/reference behavior and a typed supported deprecation adapter. Benchmark/profiler/tracemalloc observations run in the guarded standalone demo, separately; library import/runtime never controls borrowed tracing. Trusted maintainer subprocesses run 61 cases, build/install actual artifacts and compose six prior/current packages with generic old/new callers. The academy API serves bytes/stores reported evidence only; count bounds are not deadlines/byte budgets and namespace/revision does not enforce authorization/freshness. Four criteria preserve manual interpretation (ADR 0023).

## Local ingestion-persistence lab

The fixed eleven-file starter is a separate installed Psycopg package with packaged schema/typing resources. Caller-owned connections must be idle non-autocommit READ COMMITTED; the library owns one transaction/cursor, never setup/closure of the connection. Stable append-only key/value identity separates exact repeats from whole-batch conflicts. Trusted maintainer subprocesses build/install four prior/current packages and use an owned disposable PostgreSQL container; the academy API serves bytes and stores reported evidence only. This does not change academy schema, existing isolated runner or establish full deployment/concurrency/recovery (ADR 0024).

## Local ingestion-service lab

The nineteen-file authenticated starter is a separate FastAPI/Pydantic/SQLAlchemy/Alembic package. It borrows an explicit PostgreSQL Engine, snapshots caller-configured namespace credentials, checks permission before opening a request Session and returns success only after the service transaction commits. Synchronous routes use synchronous ORM work. Output models materialize allowed values; scoped keyset pages remain positions over changing data. Packaged migrations install schema outside requests; readiness checks the expected head, separately from metadata drift.

Trusted maintainer subprocesses build/install five packages, run all 70 cases on an owned disposable PostgreSQL 17 container, compose prior Record/Row/Reading/Snapshot values and start/stop the supplied installed loopback server. The academy serves authored bytes and stores reported/manual evidence; it never imports learner code, runs this service or shares its database credentials. The academy database/schema and isolated coding runner are unchanged. This bounded local evidence does not establish multi-writer stress, durable recovery or full deployment (ADR 0025).

## Local competing-ingestion extension

The thirteen-file authenticated starter depends on the completed prior ingestion-service wheel and leaves its HTTP/auth/schema contracts unchanged. It copies bounded exact Datum values before attempts, owns a fresh Session/transaction per allowed retry and closes it before a borrowed delay. A supplied after_begin Connection hook checks READ COMMITTED and applies bound transaction-local lock/statement limits. Only 40001/40P01 restart; uncertain communication outcomes stop for reconciliation.

Reconciliation owns a scoped read of requested full key/value facts and never changes data or grants permissions. Supplied separate-owner experiments observe real blocker edges, visibility, deadlocks/serialization/timeouts and cleanup in disposable schemas. Trusted maintainer subprocesses build/install the two packages and evaluate 70 finite cases plus actual JSON/previous-API permissions. The academy serves bytes and stores manual evidence only; neither learner code nor a lab database connection runs in its API. Existing runner contracts/academy schema stay unchanged. Finite two-writer evidence does not establish load fairness, durable recovery or full deployment (ADR 0026).

## First durable outbox extension

The fourteen-file authenticated starter depends on completed prior service and competition wheels. Three functions own separate Sessions: record commits strict copied facts and stable intents together, publish_one holds one scoped pending row lock until exact callback acceptance/ack commit, and consume commits its full-key inbox and aggregate effect together. The unchanged prior HTTP POST does not enqueue; matching prior facts are adopted explicitly through record. No new academy endpoint, runtime dependency, schema migration or learner execution is introduced.

Explicit one-time schema.sql adds outbox/inbox/effect tables after service_002 in a disposable schema. It is not a production Alembic migration; the prior package drift checker will identify these extra teaching tables. Resource/type packaging and installed behavior are verified. Separate pools keep worker/consumer ownership independent. Callback duration is not bounded by statement limits; bounded leases/fencing are delivered separately in ADR 0028. Real os._exit subprocesses stop at three boundaries while PostgreSQL stays alive, and an observer verifies child connection disappearance before inspecting/replaying. The durable sink models a database effect, not a broker/external email/payment contract. Trusted maintained code runs outside the academy API only (ADR 0027).

## Leased worker extension

A separate installed package borrows the existing PostgreSQL Engine and Event/Accepted interfaces. Short Sessions persist worker_policy and delivery_job, adopt up to 64 missing intents, close up to 64 expired final leases, and claim one eligible job with SKIP LOCKED. Generation increases per committed claim; Event identity stays unchanged. Claim commits/releases before publication. Scope policy remains immutable, so restarts cannot silently extend attempts or erase backoff.

Settlement locks the job and checks current generation, full key/value, exact saved deadline and a live clock_timestamp in the guarded UPDATE. Completion and outbox acknowledgment share one transaction. Explicit retries save next_at from settlement time; expired claims use lease_until plus the corresponding delay. Poison/exhaustion preserve an unacknowledged intent in dead state. No implicit redrive, renewal or SQL retry. Concurrently mixing old row-lock and new leased publishers on the same jobs is unsupported.

Sequential run checks a borrowed Event before each claim and bounds committed admissions. It finishes admitted work cooperatively, re-raises original ordinary failures after attempting retry settlement, and relies on expiry after abrupt exits. Authored main-thread process fixtures install/restore their own signal handler; imports do not alter signals. Two actual os._exit boundaries and an observed SIGTERM prove finite process behavior while PostgreSQL stays alive. Tokens fence this local database writer, not arbitrary external effects or malicious callers. Additive resource DDL remains disposable teaching setup; production migrations, operational redrive/retention and broker contracts remain separate (ADR 0028).

## Redis Streams and versioned event delivery

A separate installable package depends on the four completed local packages and redis-py 6.4.0. No academy runtime/migration/React/runner change; redis-py is added only to maintainer development requirements. Two envelope reader shapes map to the same Event(namespace,id,revision,value). Strict bounded JSON rejects duplicate/non-finite fields, unknown versions, extra/missing keys and wrong scope before effects. The publisher defaults to version two without rewriting older entries.

The supplied adapter borrows the configured client pool and leases one dedicated connection for XADD followed by checked WAITAOF 1 0 1000. Accepted means that stated local AOF boundary; producer outbox completion precedes independent consumer application. An unconfirmed append may still exist, so retry keeps Event identity and can create multiple stream IDs. Redis group setup is explicit at 0-0, with no implicit position reset or import-side infrastructure creation.

Consumer delivery/reclaim validates an envelope, commits through the existing inbox/aggregate transaction, then XACKs its transport ID. Unknown/conflicting payloads remain pending. Recovery exposes the XAUTOCLAIM cursor and deleted pending IDs, rather than claiming global emptiness or reconstructing lost payloads. XACK is not owner fencing or payload deletion. Real child exits 91/92 and observed lease/idle recovery plus an actual controlled AOF restart establish the named boundaries, not power loss/failover/external exactly-once. Owned container/network/AOF volume and private configuration are removed after checks (ADR 0029).


## Versioned local delivery schema

Six ordered lessons (python-delivery-revisions through python-migration-evidence), twelve original scenarios under separate Delivery migration contracts, and complete guided/diagram/glossary/private recall layers connect to the Delivery migration lab. Its authenticated sixteen-file starter has three unfinished functions, 44 public cases (25 offline/19 live) and four manual criteria. Six freshly built/installed packages on PostgreSQL 17.11 verify an unchanged service_001/002 plus delivery_003/004 chain, all-field/timestamp preservation without implicit enqueue, combined metadata/head/autogenerate comparison, actual late upgrade/downgrade rollback, cooperating advisory locks/real DDL timeout, explicit destructive targets and retained facts versus lost delivery history. Actual Redis composition preserves prior contracts; old service /ready intentionally reports 503 at the new head. Re-upgrade has empty inbox history and can apply the same key again. Finite reported evidence does not award mastery (ADR 0030).

The extension copies immutable prior service revision resources and adds ordinary transactional DDL revisions. A separate MetaData copies prior service tables without mutating their Base and declares the five delivery/worker tables. Explicit wrappers own one PostgreSQL transaction, set local SQL limits and take a database-wide cooperating advisory lock. No stamp, create_all, legacy setup adoption or import/request migration is supplied. The previous service business API is unchanged; its old readiness expectation requires release coordination with the new inspect_state/check workflow. The academy never imports this package or migrates its own database through it.


## Delivery retention and explicit redrive

Four ordered lessons (python-dead-job-inspection through python-recovery-evidence), eight original scenarios under separate Delivery recovery contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery recovery lab. Its authenticated twelve-file starter has three unfinished functions, 36 public cases (14 offline/22 live) and four manual criteria. Seven installed packages on owned PostgreSQL/Redis verify bounded inspection, one concurrent redrive success, preserved Event/generation/policy, exhausted refusal, stale-lease refusal, local rollback, atomic current-group payload checks and duplicate-safe replay with all local history retained. Payload deletion can survive later call failure. Reported evidence does not award mastery (ADR 0031).

The recovery extension uses the unchanged delivery_004 schema. Explicit poison redrive changes readiness under full Event/generation/policy guards and never resets budgets. Exact-id retention deletes only Redis payloads after local completion and atomic current-group checks, preserving PostgreSQL facts/intents/inbox/effects/jobs. Future group history loss and the broker/database failure gap are explicit. New schema/age policy, exhausted replacement and public operational recovery remain outside this unit (ADR 0031).


## Local release operating boundary

Four ordered lessons (python-release-settings through python-release-evidence), eight original scenarios under Release operating contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery release lab. Its authenticated fourteen-file starter has three unfinished functions, 33 public cases (15 offline/18 live) and four manual criteria. Eight installed packages on owned PostgreSQL/Redis verify private copied settings, compatible delivery_004 readiness, preserved business contracts, real failures, one owned disposal, installed operating commands/loopback SIGTERM cleanup and exact rollback losses with re-upgrade. Reported evidence does not award mastery (ADR 0032).

The parent release declares compatible /health and /ready before mounting the unchanged service. It owns its Engine/lifespan and snapshots authority; the child borrows it. Import/construction never connects or migrates. Explicit commands operate only a separate disposable lab schema; no academy schema/runtime dependency or runner contract changes. The API serves authored bytes and stores manual evidence, never imports learner code.


## Local SQL query analysis boundary

Five ordered lessons (python-query-joins through python-query-evidence), ten original scenarios under SQL query analysis contracts and complete guided/diagram/glossary/private recall layers connect to the SQL query analysis lab. Its authenticated nineteen-file starter has three unfinished SQL queries, 36 public cases (23 offline/13 PostgreSQL) and four manual criteria. Nine installed packages verify complete-key/fanout/empty reports, zero-safe revision windows, newest-before-JSONB filtering, read-only owned queries, source compatibility and actual result-equivalent baseline/indexed plans on 40,000 records/notes. Five literal lesson SQL examples also run on PostgreSQL. Reported evidence does not award mastery (ADR 0033).

The installable extension borrows an explicit PostgreSQL/psycopg2 Engine and owns each fresh read-only transaction; callers keep engines. Its separate reporting schema references the unchanged delivery_004 source schema by complete foreign key. Fixtures add/drop source B-tree and report GIN indexes explicitly, then compare original source metadata. No automatic query-time schema work, academy migration/dependency, HTTP route or runner contract changes. Only trusted maintainer subprocesses run these resources; the API serves bytes/stores manual evidence.


## Local API depth boundary

Five ordered lessons (python-http-validators through python-api-depth-evidence), ten original scenarios under separate API delivery contracts and complete guided/diagram/glossary/private recall layers connect to the API depth lab. Its authenticated fourteen-file starter has three unfinished functions, 51 public cases (39 offline/12 PostgreSQL) and four manual criteria. Nine freshly installed packages verify private conditional GET/permission ordering, framed raw-byte HMAC/freshness/strict events, atomic scoped receipts/readings, real competing duplicates/conflicts/rollback/lock timeout and compatible prior routes. The saved actual loopback HTTP report observes 200/304/change, 401/403/409/422/503/retry, committed counts and released connections. Reported tests and manual review do not award mastery (ADR 0034).

The extension borrows an explicit Engine, copies bearer/signing authority and mounts unchanged old business routes after new /v1 routes and compatible readiness. It never imports into the academy, connects on construction, owns caller engine disposal or creates schema on requests. Explicit generated fixture DDL adds/drops only a receipt table before original delivery_004 metadata comparison. Sync PostgreSQL acceptance is offloaded from the async raw-body route. New GET reads one bounded representation with read-only local SQL limits; 304 still requires a fresh permitted read. The academy serves authored bytes/stores manual evidence only.


## Composed advanced Python practical review

Five lessons (`python-practical-contracts` through `python-practical-review`), ten original scenarios and complete guided/diagram/glossary/private recall layers connect to the Composed Python practical review lab. Its authenticated eighteen-file starter has three unfinished functions, 50 public cases (47 offline/three PostgreSQL) and four manual criteria covering all seven advanced review dimensions. Eight freshly installed local packages compose strict old service pages, latest/conflict/domain adapters, immutable typed snapshots, response/resource ownership, bounded cache and actual thread/spawn workers. A stated 128-fact workload gives equivalent reporting outputs with 152/32 computations and 120 hits; a cyclic case gives 64/64 and zero hits. Actual cProfile call counts, raw wall/CPU intervals and Python allocation observations have no speed threshold. The original-case/regression/design task feeds fixed manual submissions and revisions. Maintainer fixtures and reported tests never establish learner originality, mastery or expertise (ADR 0035).

The lab stays outside the academy runtime. Supplied scaffold owns a generated service_002 fixture, loopback server and worker files; it borrows the configured async client and never hands a live Engine to workers. Imports/factories/requests have no new DDL. Later delivery_004/query/API contracts remain separate and unchanged. The academy serves allowlisted bytes and stores reported/manual evidence; it never executes uploaded code.


## Offline model contracts

Six lessons (`model-request-contracts` through `model-contract-evidence`), twelve original scenarios under separate **Model call contracts** and complete guided/diagram/glossary/private recall layers connect to the Model contracts lab. Its authenticated fourteen-file starter has three unfinished functions, **84 offline public cases** and four manual criteria. A clean installed standard-library package normalizes two invented provider formats; checks pinned model/prompt/schema, copied complete-envelope context/output admission, strict complete/refused/incomplete proposal/usage variants; and reserves fictional credits before attempts, settles only valid usage, retains unknown reserves and stops at cost/step/one cooperative deadline boundaries. Actual waiting fixtures verify timeout cleanup and propagated external cancellation. Installed JSON records eleven finite cases without raw prompts/refusal reasons/exceptions. No real model, network, current pricing, provider conformance or semantic quality is claimed (ADR 0036).

The package stays outside the academy API and runner. Configured Adapter borrows an async Transport; it sends immutable serialized requests and passes raw untrusted fixture bytes to the decoder. No imports/factories/runs acquire network/database resources or execute learner/generated code. Frozen application values keep provider wire variants outside business code. A finite per-run ledger is distinct from persistent account quotas/billing; external cancellation produces no durable report.


## Scoped retrieval contracts

Six lessons (`retrieval-chunk-identities` through `retrieval-evidence`), twelve original scenarios under separate **Scoped retrieval contracts** and complete guided/diagram/glossary/private recall layers connect to the Scoped retrieval lab. Its authenticated fifteen-file starter has three unfinished functions, **83 public cases** and four manual criteria. The installed standard-library package preserves complete chunk keys/character offsets/digests, validates model/version/dimensions/finite nonzero vectors, chooses latest revisions before trusted tenant/group/activity/metadata filters, then computes exact cosine or simple ASCII token-set Jaccard ranking with full-key ties. Requested-k precision, labelled recall and first-relevant rank use explicit denominators; no-label cases have null recall/rank and separate unwanted-hit counts. Four computed reports use an original 12-revision/15-chunk/nine-query development fixture with hand-supplied six-dimensional vectors. No real embedding model, ANN/database index, held-out quality, durable document lifecycle or automatic mastery is claimed (ADR 0037).

This standalone lab remains outside the academy API and private runner. The app supplies Principal separately from user/query text; copied frozen values and full tenant/document revision keys make ownership explicit. Known package resources are loaded on demand, never at import. Validation bounds the fixture, not physical isolation or host execution. Coherent current corpus metadata is an input assumption, not an atomic reindex/deletion implementation.


## Local evidence-answering composition

Six simple lessons (`rag-source-lifecycle` through `rag-practical-evidence`), twelve original scenarios under separate **Evidence answering contracts** and complete guided/diagram/glossary/private recall layers connect to the Evidence answering lab. Its authenticated fifteen-file starter has three unfinished functions, **70 public cases** and four manual criteria. The installed `academy-rag-lab==0.1.0` composes the published model and retrieval packages. A separate local SQLite index atomically publishes complete revisions, retains deletion markers and rejects older/conflicting publication. Trusted access filters, a stated task-term gate, keyword reranking and whole-passage UTF-8 packing select evidence before a bounded controlled call. Exact selected excerpts become citations only after current permissions, source identity and index epoch are rechecked. Missing evidence, invalid output and stale authority return no answer text. Seventeen computed experiments observe lifecycle, refusal, invalid proposals, admission, cancellation and freshness. Controlled quotes and hand-assigned vectors do not evaluate semantic answer quality or production authorization; manual submissions never award mastery (ADR 0038).

The local learner package uses the previous public Request/Adapter/Provider and configured model limits, but owns a distinct `rag-quotes-v1` output schema; it does not reuse the triage decoder. Index construction is quiet; explicit initialization and each operation own/close their SQLite connections. No transaction spans the provider await. `publish` uses one immediate transaction for complete source/vector/ACL metadata replacement and epoch increment. Tombstones retain the latest document revision, so reopen cannot restore old content. Same-revision exact replay changes nothing; older or conflicting data is rejected. Local caps include tombstones. SQL or validation failure rolls back all changes.

`prepare` composes the prior exact cosine access/metadata filters, a limited application-owned ASCII task-term gate and deterministic keyword reranking. It packs one to three whole passages with local evidence IDs, full source keys, offsets and digests; it never slices text to fill a budget. `answer` refreshes an application-owned Principal before use and after a valid proposal, compares the reconstructed bundle/current epoch and resolves every citation against current source state. Any epoch change invalidates the old plan conservatively. This final observation is not a promise that permissions will never change later; future reuse must resolve again. There is no answer cache, tool execution, URL fetch or learner execution in the academy API. The controlled standard-library lab runs separately (ADR 0038).


## Local authorized tool orchestration

Six simple lessons (`tools-proposal-boundaries` through `tools-practical-evidence`), twelve original scenarios under separate **Authorized tool contracts** and complete guided/diagram/glossary/private recall layers connect to the Authorized local tools lab. Its authenticated fifteen-file starter has three unfinished functions, **81 public cases** and four manual criteria. The installed `academy-tools-lab==0.1.0` composes model, retrieval and RAG packages. Strict proposals cannot grant authority; current application actor/principal/source checks and exact action approval precede effects. One local transaction commits a note and its scoped receipt under a stable application operation ID independent of model call IDs. Same actions replay, changed actions conflict, caps and late SQL failures are observed. One cooperative whole-loop deadline and context/cost/step budgets stop uncertain outcomes without automatic effect retries. Seventeen computed experiments observe actual calls, notes/receipts, lost-result reconciliation and cancellation; public reports redact source text and pin provider/model/prompt/schema. Controlled local evidence is not real model quality, production authority or distributed exactly-once; manual submissions never award mastery (ADR 0039).

The lab remains outside the academy runtime and runner. It borrows public model Request/Provider/Adapter/configuration and current RAG citation resolution. Context/Authority are application values, never proposal fields. The only fixed tools read a selected excerpt or save a bounded label/source digest in a separate explicitly initialized SQLite store. Neither accepts network URLs, commands or arbitrary paths. A canonical exact-action digest identifies approved parameters; trusted application Authority supplies the grant. A digest alone is not authority or a signing system.

The stable (tenant,actor,application operation_id) receipt is independent of regenerated model call IDs. One immediate transaction checks replay/conflict and caps, inserts note/receipt and commits or rolls back both. Connections close and none span awaits. Context authority and every selected source are refreshed before requests, after proposals, immediately before effects and after tool waits. Public reports redact excerpt text; only fresh permitted prompt history receives read results. One shared cooperative deadline covers provider/tool steps. A post-commit hook observes a lost result, not an invented failure; explicit same-operation replay reconciles after reopen. A committed note is historical and cannot confer current source access (ADR 0039).


## Controlled AI release and path audit

Six simple lessons (`ai-release-cases` through `ai-release-review`), twelve original scenarios under separate **AI release evidence** and complete guided/diagram/glossary/private recall layers connect to the Controlled AI release evaluation lab. Its authenticated fifteen-file starter has three unfinished functions, **54 public cases** and four manual criteria. Five installed packages execute eighteen versioned development cases for each of two candidates: **36 actual observations**. Requested-k precision is **1/4** and positive-label recall/MRR **1/2**; raw cosine has **one** unlabelled unwanted hit and the stated task-term gate has **zero**. Exact answer/tool contracts, permission/privacy/boundary counts, dataset/candidate digests and inclusive rational thresholds remain separate from two pending semantic reviews. Reports redact raw contents; role/URL/extra-field, stale-source and post-commit timeout paths are observed. The separately labelled mutation demonstrates evaluator rejection rather than claiming another provider run. Controlled development data and hand vectors do not establish real model quality or production security (ADR 0040).

The standalone evaluation package loads a strict bounded versioned case resource on demand and runs the four published AI packages in per-case owned directories. It remains outside the academy runtime/runner and removes its temporary source/note databases in the guarded demo. The application never executes uploaded evidence. A canonical dataset digest pins the policy; candidate digests include safe observed outcomes, source digests and provider/model/prompt/schema identities. Fixed complete scenario coverage and exact typed observations prevent missing/mixed cases from silently inflating metrics. Fraction arithmetic preserves denominator and threshold boundaries.

Human review is explicit reported data tied to case/dataset/candidate, with source/verdict/reviewer/note. Missing reviews remain pending and rejection cannot be averaged away. The local package does not authenticate a reviewer or judge source truth. Structural path audit verifies catalog/layer/dependency/manifest consistency; API tests exercise every published lesson and starter route. Old definitions and fixed history are preserved rather than regraded (ADR 0040).

## Comprehensive exam and portfolio boundary

The portfolios router serves three fixed briefs and seven-file authenticated build packs. Comprehensive workspaces extend frozen ExamAttempt with flags/position/code/stage and store exact source/result in ExamRun. The API calls the existing private Docker controller using frozen identity/version/execution digest; it never interprets source. Submission atomically creates a fixed server-generated review attachment with pinned rubric. Only invited accounts can review it; a later revision drops the generated attachment and retains its parent. Timers are advisory elapsed time. Knowledge exact-set scoring excludes written answers; design/repair have no invented manual percentage. See ADR 0041.

## Everyday operational boundary

Accounts owns offline one-use recovery/password/session controls; exports builds private allowlisted account evidence from the existing public domain serializers. Recovery and mutations share owner-row locking/session rechecks, while exports also lock owned submitted versions during collection. Additive account_recovery_keys stores only key digests and use timestamps. The API never runs backup tools or learner code. Trusted maintenance CLIs snapshot/restore into new databases outside requests. Five-service Compose separates maintenance role preparation from app-role migration and non-root serving; readiness verifies the actual head/database and liveness is separate. See ADR 0042 and OPERATIONS for concrete ownership/recovery and finite acceptance limits.
