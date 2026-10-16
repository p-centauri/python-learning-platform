# Curriculum map

Audience: experienced JavaScript/Vue/PostgreSQL developer. The current release has 195 authored lessons and 390 distinct objective exercises across 43 modules. Python foundations is a nine-lesson path to a bounded expense-tracker CLI project, followed by a five-lesson text/time/debugging module and event-timeline repair lab, then ownership, a five-lesson object-design/typing module, five lessons on streaming/resource cleanup, eight packaging/HTTP ingestion lessons, seven function/testing/diagnostic lessons, eight async/work-limit lessons, six advanced object-behavior lessons, seven advanced typing/interface lessons, six advanced context/resource lessons, seven thread/process lessons, eight measurement/cache/compatibility lessons, eight PostgreSQL persistence lessons and eight ingestion-service lessons, seven competing-transaction lessons, six durable-outbox lessons, six leased-worker lessons, six broker/event-evolution lessons six delivery-migration lessons four retention/redrive lessons and four release operations lessons and five SQL query analysis lessons and five API depth lessons. Of the 18 non-Python modules, 13 remain introductory slices; model-contract, scoped-retrieval, evidence-answering, authorized-tool and controlled release-evaluation practice add connected local labs. This is not the full curriculum. Unauthored tracks remain explicitly planned.

## Advanced Python
The complete Python teaching sequence, including beginner prerequisites, is planned in [Python learning path](docs/PYTHON_LEARNING_PATH.md). One hundred and forty-seven dedicated Python lessons are authored: nine foundations, five practical continuation, ownership, five object-design/typing, five streaming/resource-cleanup, eight packaging/HTTP ingestion lessons, seven function/testing/diagnostic lessons, eight async/work-limit lessons, six advanced object-behavior lessons, seven advanced typing/interface lessons, six advanced context/resource lessons, seven thread/process lessons, eight measurement/cache/compatibility lessons, eight PostgreSQL persistence lessons and eight ingestion-service lessons, seven competing-transaction lessons, six durable-outbox lessons, six leased-worker lessons, six broker/event-evolution lessons six delivery-migration lessons four retention/redrive lessons and four release operations lessons and five SQL query analysis lessons and five API depth lessons. The foundations path covers setup, values, collections, loops, functions, errors, files, CLI design and tests; it includes a downloadable local project. The continuation covers UTF-8/Unicode, collections, timestamp validation, zones/durations and pdb-based repair. The object-design module adds a typed task-inbox project with 14 runtime tests and a static type-checking exercise. The streaming module adds a service-log lab with 16 tests covering lazy input, bounded reads, errors and owned cleanup. The installable ingestion module adds 28 offline public tests, typed HTTP boundaries, chunk framing, cleanup, dependency workflow and clean artifact verification. The policy extension adds 49 pytest cases covering independent closures, explicit signatures, transparent wrappers, fixtures, patching, safe logs and bounded regex. Its wheel composes with prior ingestion through a read-only protocol. The async lab adds 75 public cases, typed installed selector composition, bounded queues/workers and observable cooperative shutdown. The feed-object lab adds 50 cases for per-object descriptors, immutable feed identity and bounded ordered snapshots, with installed prior-record adaptation and four manual criteria. The transformation lab adds 47 runtime cases and one positive/ten rejected checker fixtures for generics, preserved call shapes, precise overloads and validated boundaries; installed adapters preserve previous contracts. The resource-scopes lab adds 54 cases for partial handoffs, reverse cleanup/error chaining, awaited cancellation, token restoration and non-owning weak lookup, plus installed prior-value composition. The bounded offload lab adds 66 cases for ordered admission, queued/running cancellation, worker-local parsing and joined thread/spawn ownership, with installed prior-value composition. The measured-cache lab adds 61 cases for finite raw intervals, LRU/key/failure/reference behavior and compatible deprecated callers; its installed demo records actual timing/profile/allocation evidence without speed gates. The three Python tests sample knowledge and do not mean this curriculum is complete.

Reason about object identity, resource ownership, types and concurrency.

- Objects and ownership
- Scope and closures
- Decorators and protocols
- Iteration and generators
- Context managers and exceptions
- Typing and generics
- Packaging
- Async and parallelism
- Profiling

## Backend engineering with FastAPI
Design explicit boundaries and reliable request lifecycles.

- Routing and validation
- Dependencies
- Authentication and authorization
- SQLAlchemy and Alembic
- Domain and service layers
- Pagination and API contracts
- Webhooks and WebSockets
- Observability

## Django & Django REST Framework
Use a productive framework without hiding query and permission costs.

- ORM and migrations
- Managers and querysets
- Signals
- Middleware
- Authentication
- Admin
- Serializers
- Viewsets
- Permissions
- Throttling
- Celery
- N+1 diagnosis

## PostgreSQL mastery
Make invariants survive concurrent requests and operational failures.

- Modeling and constraints
- Index structures
- EXPLAIN ANALYZE
- Joins and CTEs
- Window functions
- JSONB
- MVCC and isolation
- Locks and deadlocks
- SKIP LOCKED
- Pooling
- Partitioning
- WAL and vacuum
- Replication and security

## HTTP & API engineering
Treat timeouts, retries and contracts as part of API correctness.

- DNS TCP TLS
- HTTP versions
- Methods and status codes
- Caching and ETags
- CORS and cookies
- Cursor pagination
- Idempotency
- Backoff and jitter
- Circuit breakers
- OAuth2 OIDC JWT

## Software architecture
Choose boundaries and patterns according to concrete failure modes.

- SOLID DRY KISS YAGNI
- Cohesion and coupling
- Ports and adapters
- Repository and Unit of Work
- Domain modeling
- Modular monolith
- CQRS
- Outbox and inbox
- Saga
- Bulkheads and dead letters

## Distributed systems
Reason about partial failure, consistency and duplicate delivery.

- Partial failure
- Delivery semantics
- Ordering
- Idempotency
- Consistency
- Transactions and Saga
- Consensus
- Leader election
- Clocks
- CAP
- Backpressure
- Sharding
- Recovery

## Redis, queues & workers
Control asynchronous work without assuming a perfect broker.

- Redis data structures and TTL
- Cache invalidation
- Atomic operations
- Locks
- Pub/sub and Streams
- Celery
- RabbitMQ acknowledgements
- Retries
- Poison messages
- Kafka partitions groups offsets

## Testing engineering
Build evidence that catches failures rather than flattering coverage.

- Unit integration functional E2E contract regression tests
- Property testing
- Load and chaos tests
- Mocks fakes stubs
- pytest
- Async and database tests
- Testcontainers
- Mutation testing

## Production engineering
Ship, observe, roll back and recover services deliberately.

- Linux processes signals sockets permissions
- Nginx
- Docker layers networking volumes secrets
- Health and shutdown
- Migration rollouts
- Git
- CI/CD
- GitHub Actions
- Security scans

## Observability
Explain user-visible failures using logs, metrics and traces.

- Structured logs
- Correlation
- OpenTelemetry
- Prometheus
- Grafana
- Alerting
- SLIs SLOs
- Error budgets
- Tail latency
- Incident investigation

## Cloud & AWS
Translate reliability and cost constraints into infrastructure choices.

- IAM VPC EC2 S3 RDS ElastiCache
- ECS ECR
- SQS SNS
- CloudWatch
- Secrets Manager
- ALB
- Auto Scaling
- Route 53 CloudFront Lambda
- Regions AZs
- Backup and disaster recovery

## Application security
Make authorization and trust boundaries explicit.

- OWASP
- SQL injection XSS CSRF SSRF command injection
- RBAC ABAC
- Password hashing
- Encryption
- Cookies and JWT risks
- Secrets
- Rate limiting
- Supply chain

## System design
Begin with constraints; defend tradeoffs and failure behavior.

- Requirements and estimation
- APIs and data models
- Caches queues load balancing
- Consistency availability cost
- URL shortener
- Notifications
- Payments
- Chat
- Storage
- Analytics
- AI assistant

## LLM fundamentals
Understand probabilistic generation and its application boundaries.

- Tokens
- Context windows
- Attention
- Inference
- Model selection
- Sampling
- Hallucinations
- Structured output
- Instructions
- Context engineering
- Fine-tuning
- Privacy latency cost

## Embeddings & vector search
Measure retrieval before trusting semantic similarity.

- Vector geometry
- Cosine dot product Euclidean
- ANN
- pgvector
- Chunking and overlap
- Metadata filters
- Hybrid BM25
- Reranking

## Retrieval-augmented generation
Build answers from authorized, measurable evidence.

- Ingestion and parsing
- Chunking
- Embeddings and indexing
- Query rewriting
- Hybrid retrieval
- Reranking
- Context
- Citations
- Freshness
- Multi-tenancy
- Evaluation

## Tool calling
Give a model a constrained proposal interface to application logic.

- Schemas
- Validation
- Authorization
- Tool selection
- Retries
- Errors
- Structured responses
- Injection
- Human approval
- Audit logs

## Agent engineering
Bound loops, permissions and budgets; prefer workflows when sufficient.

- Planning execution observation
- State and memory
- Tools
- Permissions
- Checkpoints
- Human in the loop
- Workflow vs agent
- Multi-agent concepts
- Budgets and stopping

## AI security
Treat model inputs and retrieved documents as untrusted data.

- Direct and indirect prompt injection
- Exfiltration
- Tool abuse
- Privilege escalation
- Malicious URLs
- Unsafe autonomy
- Data and tenant isolation

## AI evaluation
Use reproducible datasets and measurable regressions to guide changes.

- Golden datasets
- Retrieval metrics
- Correctness groundedness faithfulness
- Tool accuracy
- Latency tokens cost
- Regression gates
- Model comparison
- A/B tests
- Judge limits
- Human evaluation

## AI observability
Trace the complete path from request to retrieved evidence and actions.

- Prompt and model versions
- Retrieval traces
- Documents
- Rerankers
- Tokens and cost
- Tool calls
- Failures
- Quality telemetry
- Privacy and redaction

## Optional ML foundations
A secondary path for understanding learning systems more deeply.

- Statistics probability linear algebra
- Gradient descent
- Supervised and unsupervised learning
- Classification regression
- Overfitting
- Validation and splits
- Neural networks
- PyTorch
- Transformers

## Dependency spine
Python ownership → FastAPI boundaries → production lifecycle. PostgreSQL locks + HTTP idempotency → distributed duplicates → outbox and queue recovery. LLM contracts → embeddings → RAG. LLM contracts + HTTP idempotency → tool calling. RAG + tool calling → AI evaluation and AI security. Agent engineering follows tool calling; optional ML never blocks the main path.

## Authoring
Edit `content/catalog.json` for metadata, exercise definitions and project milestones; use Markdown in `content/lessons/`. Do not copy content into React. Add stable IDs, prerequisite IDs, objectives, three progressive hints, a reasoned answer and primary-source reading. Run content validation tests and seed the catalog. Publish future incompatible edits with a new content version and an assessment migration/snapshot policy.

The eight-lesson packaging/HTTP continuation and installable lab are published after resource cleanup, followed by seven function/testing/diagnostic lessons and a separately packaged policy lab, then eight async lessons and a bounded multi-source lab, followed by six object-behavior lessons and a bounded feed-object library, then seven advanced typing lessons and a typed transformation package, then six context/resource lessons and the scoped ownership package, followed by seven thread/process lessons and a bounded offload package, then eight measurement/cache/compatibility lessons and an installed measured-cache package. Step 6 is still in progress; see [STEP_6_PATHS.md](docs/STEP_6_PATHS.md) for the connected teaching/practical acceptance ledger. Full advanced Python, backend and applied AI teaching must not be inferred from introductory lessons or knowledge evaluations.

The first persistence continuation adds eight Python/PostgreSQL lessons, sixteen scenarios and an eleven-file ingestion-persistence starter with 57 public cases. An installed reference verifies actual PostgreSQL 17 constraints, idle transaction ownership, duplicate/conflict distinctions, late rollback, second-connection visibility and bounded reads. Four criteria preserve manual evidence. Service/migration teaching is delivered in the next bounded unit (ADR 0025); bounded competing transactions are delivered in ADR 0026; the first worker process-replay unit is delivered in ADR 0027; broader durable recovery remains later work.

The first service continuation adds eight Python/backend lessons from python-http-api-contracts through python-service-evidence, sixteen original scenarios, complete interactive/recall layers and a nineteen-file ingestion-service starter. Three unfinished functions connect strict requests, per-namespace permission, explicit ORM transactions and scoped keyset pages. The installed reference passes 70 finite public cases on PostgreSQL, migration downgrade/re-upgrade and head/drift checks, typed prior-package composition and an actual loopback server. Four manual criteria require observations and interpretation. Competing transactions, indexes/EXPLAIN, retry/reconciliation, durable workers and broader deployment/API security remain planned (ADR 0025).

The first competition continuation adds seven Python/PostgreSQL lessons, fourteen original scenarios and complete interactive/recall layers. A thirteen-file extension depends on the completed prior service wheel, with three unfinished functions and 70 public cases. Fresh installed PostgreSQL evidence covers observed waits, four commit/rollback races, READ COMMITTED/REPEATABLE READ snapshots, SERIALIZABLE reevaluation, actual deadlock retry, cancellation, copied input and full-key reconciliation. Four manual criteria preserve interpretation. Worker/outbox/crash recovery, broader SQL/API depth, deployment and applied AI remain open (ADR 0026).

The first durable-outbox continuation adds six lessons, twelve original scenarios and full guided/diagram/glossary/recall layers. A fourteen-file local extension has three unfinished functions and 67 public cases: 45 offline and 22 PostgreSQL-dependent. Fresh installation observes atomic recording/adoption, stable payload identity, scoped SKIP LOCKED claims, exact durable acceptance, consumer rollback and three real child process exits with replay. Four manual criteria separate interpretation. Leases/fencing, backoff/poison messages/shutdown, brokers/schema evolution, operations, broader SQL/API and applied AI remain open (ADR 0027).

## Leased worker continuation

Six ordered lessons (python-worker-leases through python-worker-evidence) add twelve original scenarios under Worker lease contracts, twelve guided choices/terms/private recall variants and six diagrams. The authenticated fourteen-file leased-worker extension has three unfinished functions and 59 public cases (35 offline/24 PostgreSQL-dependent), with four manual review criteria. Four freshly built/installed local packages on PostgreSQL 17.11 verify short committed leases, copied stable events, current-generation/live-deadline settlement, persisted retry times/attempt limits, poison/exhaustion quarantine, bounded admission, real acknowledgment rollback, two actual child exits/observed expiry/generation-2 reclaims and cooperative SIGTERM. Replay preserves one local consumer effect. Old Event/Accepted/service routes and permissions remain unchanged; reported output and checklists do not award mastery (ADR 0028).

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.

## Broker delivery continuation

Six ordered lessons (python-event-envelopes through python-stream-evidence), twelve original scenarios under separate Stream delivery contracts, and complete guided/diagram/glossary/private recall layers connect to the Broker delivery lab. Its authenticated fifteen-file starter has three unfinished functions, 74 public cases (59 offline/15 live) and four manual criteria. Five fresh installed local packages verify strict supported v1/v2 envelopes with stable Event identity, checked Redis XADD/WAITAOF local AOF acceptance on one physical connection, producer completion before consumer effects, inbox/effect commit before XACK, pending/reclaim/cursor/deleted-gap semantics, duplicate/conflicting facts, real constraints, two actual child exits and a controlled retained-AOF broker restart. PostgreSQL 17.11, Redis 7.4.2 and redis-py 6.4.0 are observed; reported evidence does not award mastery (ADR 0029).

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.


## Delivery schema and migration rehearsal

Six ordered lessons (python-delivery-revisions through python-migration-evidence), twelve original scenarios under separate Delivery migration contracts, and complete guided/diagram/glossary/private recall layers connect to the Delivery migration lab. Its authenticated sixteen-file starter has three unfinished functions, 44 public cases (25 offline/19 live) and four manual criteria. Six freshly built/installed packages on PostgreSQL 17.11 verify an unchanged service_001/002 plus delivery_003/004 chain, all-field/timestamp preservation without implicit enqueue, combined metadata/head/autogenerate comparison, actual late upgrade/downgrade rollback, cooperating advisory locks/real DDL timeout, explicit destructive targets and retained facts versus lost delivery history. Actual Redis composition preserves prior contracts; old service /ready intentionally reports 503 at the new head. Re-upgrade has empty inbox history and can apply the same key again. Finite reported evidence does not award mastery (ADR 0030).


## Delivery retention and explicit redrive

Four ordered lessons (python-dead-job-inspection through python-recovery-evidence), eight original scenarios under separate Delivery recovery contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery recovery lab. Its authenticated twelve-file starter has three unfinished functions, 36 public cases (14 offline/22 live) and four manual criteria. Seven installed packages on owned PostgreSQL/Redis verify bounded inspection, one concurrent redrive success, preserved Event/generation/policy, exhausted refusal, stale-lease refusal, local rollback, atomic current-group payload checks and duplicate-safe replay with all local history retained. Payload deletion can survive later call failure. Reported evidence does not award mastery (ADR 0031).


## Delivered release compatibility and operations

Four ordered lessons (python-release-settings through python-release-evidence), eight original scenarios under Release operating contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery release lab. Its authenticated fourteen-file starter has three unfinished functions, 33 public cases (15 offline/18 live) and four manual criteria. Eight installed packages on owned PostgreSQL/Redis verify private copied settings, compatible delivery_004 readiness, preserved business contracts, real failures, one owned disposal, installed operating commands/loopback SIGTERM cleanup and exact rollback losses with re-upgrade. Reported evidence does not award mastery (ADR 0032).


## Delivered SQL query depth and plans

Five ordered lessons (python-query-joins through python-query-evidence), ten original scenarios under SQL query analysis contracts and complete guided/diagram/glossary/private recall layers connect to the SQL query analysis lab. Its authenticated nineteen-file starter has three unfinished SQL queries, 36 public cases (23 offline/13 PostgreSQL) and four manual criteria. Nine installed packages verify complete-key/fanout/empty reports, zero-safe revision windows, newest-before-JSONB filtering, read-only owned queries, source compatibility and actual result-equivalent baseline/indexed plans on 40,000 records/notes. Five literal lesson SQL examples also run on PostgreSQL. Reported evidence does not award mastery (ADR 0033).


## Delivered API depth

Five ordered lessons (python-http-validators through python-api-depth-evidence), ten original scenarios under separate API delivery contracts and complete guided/diagram/glossary/private recall layers connect to the API depth lab. Its authenticated fourteen-file starter has three unfinished functions, 51 public cases (39 offline/12 PostgreSQL) and four manual criteria. Nine freshly installed packages verify private conditional GET/permission ordering, framed raw-byte HMAC/freshness/strict events, atomic scoped receipts/readings, real competing duplicates/conflicts/rollback/lock timeout and compatible prior routes. The saved actual loopback HTTP report observes 200/304/change, 401/403/409/422/503/retry, committed counts and released connections. Reported tests and manual review do not award mastery (ADR 0034).


## Composed advanced Python practical review

Five lessons (`python-practical-contracts` through `python-practical-review`), ten original scenarios and complete guided/diagram/glossary/private recall layers connect to the Composed Python practical review lab. Its authenticated eighteen-file starter has three unfinished functions, 50 public cases (47 offline/three PostgreSQL) and four manual criteria covering all seven advanced review dimensions. Eight freshly installed local packages compose strict old service pages, latest/conflict/domain adapters, immutable typed snapshots, response/resource ownership, bounded cache and actual thread/spawn workers. A stated 128-fact workload gives equivalent reporting outputs with 152/32 computations and 120 hits; a cyclic case gives 64/64 and zero hits. Actual cProfile call counts, raw wall/CPU intervals and Python allocation observations have no speed threshold. The original-case/regression/design task feeds fixed manual submissions and revisions. Maintainer fixtures and reported tests never establish learner originality, mastery or expertise (ADR 0035).

This review composes selected published boundaries; it does not substitute for the remaining applied AI curriculum or prove full expert Python coverage.


## Offline model contracts

Six lessons (`model-request-contracts` through `model-contract-evidence`), twelve original scenarios under separate **Model call contracts** and complete guided/diagram/glossary/private recall layers connect to the Model contracts lab. Its authenticated fourteen-file starter has three unfinished functions, **84 offline public cases** and four manual criteria. A clean installed standard-library package normalizes two invented provider formats; checks pinned model/prompt/schema, copied complete-envelope context/output admission, strict complete/refused/incomplete proposal/usage variants; and reserves fictional credits before attempts, settles only valid usage, retains unknown reserves and stops at cost/step/one cooperative deadline boundaries. Actual waiting fixtures verify timeout cleanup and propagated external cancellation. Installed JSON records eleven finite cases without raw prompts/refusal reasons/exceptions. No real model, network, current pricing, provider conformance or semantic quality is claimed (ADR 0036).

The model-contract milestone is delivered as finite application evidence. Full-byte request units are an explicit fixture counter, not a real tokenizer or universal estimate. Real provider integration/quality/billing remains broader work. Retrieval and bounded RAG are delivered in ADRs 0037/0038; bounded tool use is delivered in ADR 0039; The final fixed milestone is verified in ADR 0040.


## Scoped embeddings and retrieval

Six lessons (`retrieval-chunk-identities` through `retrieval-evidence`), twelve original scenarios under separate **Scoped retrieval contracts** and complete guided/diagram/glossary/private recall layers connect to the Scoped retrieval lab. Its authenticated fifteen-file starter has three unfinished functions, **83 public cases** and four manual criteria. The installed standard-library package preserves complete chunk keys/character offsets/digests, validates model/version/dimensions/finite nonzero vectors, chooses latest revisions before trusted tenant/group/activity/metadata filters, then computes exact cosine or simple ASCII token-set Jaccard ranking with full-key ties. Requested-k precision, labelled recall and first-relevant rank use explicit denominators; no-label cases have null recall/rank and separate unwanted-hit counts. Four computed reports use an original 12-revision/15-chunk/nine-query development fixture with hand-supplied six-dimensional vectors. No real embedding model, ANN/database index, held-out quality, durable document lifecycle or automatic mastery is claimed (ADR 0037).

The sixth fixed milestone is delivered as bounded retrieval teaching/practice. Real embedding generation, approximate/vector-database indexing, held-out quality and production authorization remain broader work. Bounded local corpus updates/deletions and RAG are delivered in ADR 0038; bounded tool use is delivered in ADR 0039; The final fixed milestone is verified in ADR 0040.


## Verified RAG continuation (2026-10-11)

Six simple lessons (`rag-source-lifecycle` through `rag-practical-evidence`), twelve original scenarios under separate **Evidence answering contracts** and complete guided/diagram/glossary/private recall layers connect to the Evidence answering lab. Its authenticated fifteen-file starter has three unfinished functions, **70 public cases** and four manual criteria. The installed `academy-rag-lab==0.1.0` composes the published model and retrieval packages. A separate local SQLite index atomically publishes complete revisions, retains deletion markers and rejects older/conflicting publication. Trusted access filters, a stated task-term gate, keyword reranking and whole-passage UTF-8 packing select evidence before a bounded controlled call. Exact selected excerpts become citations only after current permissions, source identity and index epoch are rechecked. Missing evidence, invalid output and stale authority return no answer text. Seventeen computed experiments observe lifecycle, refusal, invalid proposals, admission, cancellation and freshness. Controlled quotes and hand-assigned vectors do not evaluate semantic answer quality or production authorization; manual submissions never award mastery (ADR 0038).

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.


## Verified tool-use continuation (2026-10-11)

Six simple lessons (`tools-proposal-boundaries` through `tools-practical-evidence`), twelve original scenarios under separate **Authorized tool contracts** and complete guided/diagram/glossary/private recall layers connect to the Authorized local tools lab. Its authenticated fifteen-file starter has three unfinished functions, **81 public cases** and four manual criteria. The installed `academy-tools-lab==0.1.0` composes model, retrieval and RAG packages. Strict proposals cannot grant authority; current application actor/principal/source checks and exact action approval precede effects. One local transaction commits a note and its scoped receipt under a stable application operation ID independent of model call IDs. Same actions replay, changed actions conflict, caps and late SQL failures are observed. One cooperative whole-loop deadline and context/cost/step budgets stop uncertain outcomes without automatic effect retries. Seventeen computed experiments observe actual calls, notes/receipts, lost-result reconciliation and cancellation; public reports redact source text and pin provider/model/prompt/schema. Controlled local evidence is not real model quality, production authority or distributed exactly-once; manual submissions never award mastery (ADR 0039).

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.


## Verified final step-six evaluation and path audit (2026-10-12)

Six simple lessons (`ai-release-cases` through `ai-release-review`), twelve original scenarios under separate **AI release evidence** and complete guided/diagram/glossary/private recall layers connect to the Controlled AI release evaluation lab. Its authenticated fifteen-file starter has three unfinished functions, **54 public cases** and four manual criteria. Five installed packages execute eighteen versioned development cases for each of two candidates: **36 actual observations**. Requested-k precision is **1/4** and positive-label recall/MRR **1/2**; raw cosine has **one** unlabelled unwanted hit and the stated task-term gate has **zero**. Exact answer/tool contracts, permission/privacy/boundary counts, dataset/candidate digests and inclusive rational thresholds remain separate from two pending semantic reviews. Reports redact raw contents; role/URL/extra-field, stale-source and post-commit timeout paths are observed. The separately labelled mutation demonstrates evaluator rejection rather than claiming another provider run. Controlled development data and hand vectors do not establish real model quality or production security (ADR 0040).

The agreed nine-milestone teaching/lab sequence is complete. [Coverage audit](docs/COVERAGE_AUDIT.md) records the actual boundaries; broader product/portfolio/reliability work remains planned.

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.

## Portfolio and comprehensive continuation

All 195 existing lessons/390 scenarios are preserved. Backend commerce, enterprise RAG and multilingual finance now have complete build contracts, ordered stable milestones, seven-file learner packs, failure/evidence matrices, libraries and review guidance. These are learner products to implement. Three separate comprehensive exams add 48 mixed knowledge questions, 23 finite repair contracts and four baseline/seven incident design artifacts. Three review workspaces bring the total to 35 without inventing mastery. See docs/STEP_7_PORTFOLIO_EXAMS.md and ADR 0041; broad expert depth and step-eight everyday reliability remain open.
