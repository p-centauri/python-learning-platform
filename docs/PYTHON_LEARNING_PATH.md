# Python learning path: foundations to expert practice

## What is actually available

The academy now has **152 dedicated Python lessons and 304 Python practice scenarios**, covering foundations through bounded advanced, service, worker and recovery units. Twenty-nine authenticated local starters connect teaching to finite implementation evidence; three additional portfolio briefs remain broader practical targets. The three Python knowledge evaluations retain **72 questions total**; there is also one Python question in the mixed diagnostic. Simple explanations and level-specific library guides are published. This is **not a complete Python course**, and passing the advanced test does not establish expertise. The complete unit ledger is in [STEP_6_PATHS.md](STEP_6_PATHS.md).

This document is a teaching plan and coverage audit. Foundations, practical text/time/debugging, object design/typing, streaming/resource cleanup, packaging/managed HTTP ingestion, functions/testing/diagnostics, bounded async ingestion, advanced object behavior, advanced typing, context/resource lifetime, thread/process concurrency, measurement/cache/compatibility, the first PostgreSQL persistence unit and the first ingestion-service unit and the first competing-transaction unit the first durable-outbox unit and bounded leased-worker, broker/event-envelope, migration/recovery/release/query and API-depth continuations are published. Full advanced practical review and applied AI teaching remain to be completed. The foundations lessons map to setup, values, collections/text, control flow, functions, errors, files, CLI/modules and tests. Their independent tasks run locally. Some other topics appear only in test questions, which do not teach the whole subject. [STEP_6_PATHS.md](STEP_6_PATHS.md) records the connected backend/applied AI continuation and its remaining acceptance work.

Each published Python lesson now includes a guided prediction, a small debugging/fix choice, a simple diagram and linked glossary terms. Submitted feedback is saved separately from reading and mastery. These finite guided questions supplement the local projects, original scenarios and delayed review; they do not complete missing teaching or certify expertise. Section links and previous/next controls follow the published Python track.

Start in the app at `/lessons/python-start`. The sequence ends at `/lessons/python-tests`, and the starter is available in Projects. A working CLI demonstrates this module’s contract, not the entire beginner syllabus. Continue at `/lessons/python-text-bytes` for five lessons on text, collections, timestamps, time zones and debugging, ending with the event-timeline repair lab. Broader edge cases still need ongoing practice.

## Stage 1 — beginner foundations

| Published and planned lesson group | Explain simply | Show skill by doing |
| --- | --- | --- |
| Setup and running code | Interpreter, terminal, REPL, scripts, environments and installing packages | Run a script in a fresh environment and explain which Python is running. |
| Values and expressions | Names, numbers, booleans, None, operators and conversion | Parse user input and distinguish missing values from valid zero values. |
| Text and bytes | Strings, slicing, formatting, Unicode and encoding | Read UTF-8 text and explain why text and bytes are different. |
| Collections | Lists, tuples, dictionaries, sets, indexing, membership and copying | Pick a collection for a task and avoid unexpected sharing. |
| Decisions and loops | if, for, while, range, enumerate, zip and comprehensions | Process empty, one-item and many-item inputs correctly. |
| Functions | Arguments, return values, defaults, local scope and small reusable functions | Split a script into functions with clear inputs and outputs. |
| Errors and debugging | Tracebacks, expected exceptions, assertions and debugger basics | Find the line that failed and fix the cause rather than hiding the error. |
| Files and simple data | Paths, with blocks, CSV, JSON and basic validation | Read a file, reject bad rows and close it after a failure. |
| Modules and basic tests | Imports, main guard, project folders and simple tests | Import functions without running the script and test edge cases. |

**Project:** an expense-report CLI that reads CSV, validates entries, writes a JSON summary and tests missing/invalid input. Review the implementation separately from the beginner test.

## Stage 2 — intermediate application building

**Available now:** after `/lessons/python-ownership`, follow `/lessons/python-classes` through `/lessons/python-protocols`. These five lessons teach per-object state, properties, dataclasses, composition, boundary validation, collection/union hints, basic protocols and testing with fakes. The downloadable task inbox supplies 14 runtime tests and a mypy exercise. Continue at `/lessons/python-iterators` through `/lessons/python-context-managers` for one-pass input, generators, memory limits, error causes and owned/borrowed cleanup. The service-log lab has 16 public tests. Continue at `/lessons/python-packages` through `/lessons/python-ingestion-tests` for eight lessons on package metadata, imports/resources, dependencies, clean artifact checks, HTTP client/response ownership, framing/byte limits, error/retry policy and offline failure tests. The installable ingestion package has 28 public tests plus verified types/lint, wheel/source-archive builds and clean installation outside source. Continue at `/lessons/python-closures` through `/lessons/python-regex-contracts` for independent closures, argument binding/defaults, transparent decorators, pytest fixtures/case tables, fakes/patching, safe logging and bounded regex. The separate feed-policy lab supplies 49 public cases and four review criteria. Continue at `/lessons/python-coroutines` through `/lessons/python-async-tests` for coroutines, TaskGroup failures, cancellation, total cooperative budgets, bounded queues/workers, async resource ownership and HTTPX AsyncClient streams. The async-feed lab has 75 public cases and four manual criteria. Continue at `/lessons/python-attribute-lookup` through `/lessons/python-object-contracts` for six advanced object-behavior lessons and a 50-case feed-object lab with four manual criteria. Continue at `/lessons/python-generic-functions` through `/lessons/python-typed-interfaces` for seven advanced typing lessons and a typed transformation lab with 47 runtime cases, positive/ten rejected checker fixtures and four manual criteria. Continue at /lessons/python-exit-stack through /lessons/python-resource-contracts for six lessons and the 54-case ownership lab. Continue at /lessons/python-thread-process through /lessons/python-offload-contracts for seven thread/process lessons and a 66-case bounded offload lab. Continue at /lessons/python-measurement-baselines through /lessons/python-measurement-contracts for eight measurement/cache/compatibility lessons and a 61-case lab with actual installed timing/profile/allocation evidence. The first PostgreSQL transaction unit is published separately; the bounded service and composed practical-review units are published; broader expert/production evidence remains open.

| Published and planned lesson group | Explain simply | Show skill by doing |
| --- | --- | --- |
| Function behavior | Closures, argument binding, decorators and mutable defaults | Explain when values are captured and build a small tested decorator. |
| Classes and object design | Instance/class attributes, dataclasses, properties, composition and inheritance | Keep per-object data separate and choose simple interfaces. |
| Iteration | Iterables, iterators, generators, yield and lazy processing | Process a large input without keeping it all in memory. |
| Resource cleanup | Context managers, finally, custom errors and error causes | Release resources and keep useful error messages when work fails. |
| Type hints | Collections, unions, generics and basic protocols | Run a type checker and validate data arriving from outside the program. |
| Everyday library work | Dates/time zones, Decimal, collections, logging, regex and CLI parsing | Handle real inputs with clear rules for dates, money and errors. |
| Testing design | Fixtures, parametrization, fakes, mocks, integration tests and coverage limits | Test a failure without replacing the very code being tested. |
| Network and data access | Managed HTTP clients, timeouts, SQL parameters and transactions | Build a small service with safe input and predictable failures. |
| Async basics | Coroutines, tasks, await, cancellation and concurrency limits | Run independent I/O with bounded work and reliable cleanup. |
| Packaging and workflow | pyproject.toml, dependency declarations, lint, types and CI | Install and test a package in a clean environment. |

**Published project:** an installable synchronous data-ingestion package with typed inputs, streamed parsing, a managed HTTP client and failure tests. Four pinned criteria support self/human review and revisions. It has no automatic retries, database writes or async jobs. A reviewer should check behavior, not just whether the test suite is green. The separately packaged async continuation is now published, with bounded multi-source work and shutdown evidence; database persistence and the first service unit are published separately; competing transactions and recovery remain planned.

## Stage 3 — advanced Python reasoning

The published async unit introduces TaskGroup/exception groups, cancellation and async context ownership through one bounded lab. Broader structured-concurrency patterns remain continuation work; contextvars/weak references and dynamic cleanup are published separately; the six object-behavior lessons and feed-object lab are now published. Seven advanced typing lessons and the transformation lab are also published. Six context/resource lessons and the 54-case lab are published. Seven thread/process lessons and the 66-case offload lab are also published; eight measurement/cache/compatibility lessons and the 61-case lab are published separately. The first PostgreSQL persistence and service units are published; bounded competing transactions/retry/reconciliation are published; the first outbox/process-replay unit is published; the bounded leases/backoff/quarantine/shutdown unit is published in ADR 0028; the bounded broker/event-envelope unit is published in ADR 0029; bounded delivery migrations are published in ADR 0030; bounded retention/redrive is published in ADR 0031; release compatibility remains next.

| Published and planned lesson group | Explain simply | Show skill by doing |
| --- | --- | --- |
| Object model | Attribute lookup, descriptors, MRO, special methods, equality and hashing | Predict lookup behavior and preserve dictionary-key rules. |
| Advanced typing | Variance, ParamSpec, protocols, overloads and type narrowing | Publish a useful typed interface without hiding errors behind casts. |
| Advanced resources | ExitStack, async context managers, contextvars and weak references | Handle partial setup failure and restore request-specific state. |
| Structured async work | Task groups, exception groups, cancellation and bounded queues | Stop related tasks safely and avoid unlimited waiting work. |
| Threads and processes | Locks, races, GIL/build differences, spawn and serialization | Choose an execution model and measure its costs. |
| Memory and speed | Profiling, complexity, allocation tracing, cache lifetime and benchmarking | Find a real bottleneck and show a measured improvement. |
| Imports and distribution | Import behavior, wheel contents, package resources and compatibility | Test what users install, outside the source checkout. |
| Robustness and security | Unsafe deserialization, command execution boundaries, secrets and dependency review | Explain trust boundaries and test malformed/untrusted inputs. |
| Library design | Public APIs, deprecation, documentation and extension points | Evolve a package without surprising its callers. |

**Project:** the bounded ingestion service and external review rubric in [PYTHON_LEVELS.md](PYTHON_LEVELS.md). The advanced knowledge test samples seven topic groups; it does not cover every row here or automatically review the project.

## Stage 4 — expert practice in a chosen domain

Expertise develops through repeated implementation, debugging and review. There is no single package list or fixed quiz score that proves it.

- Maintain a real package or service across releases, including compatibility and migrations.
- Diagnose failures from incomplete evidence: crashes, deadlocks, slow requests, memory growth and cancellation bugs.
- Design failure tests, benchmarks and observability that help another engineer reproduce the problem.
- Read Python documentation, relevant PEPs and library source to resolve questions instead of relying on guesses.
- Review other people's code, explain tradeoffs plainly and revise decisions when measurements disagree.
- Specialize where useful: backend services, data/AI, automation, or native extensions. C APIs, Cython/Rust bindings and deep interpreter internals are specialized paths, not requirements for every Python expert.

**Evidence:** a maintained project, meaningful reviews, incident write-ups, performance reports and fixes verified by regression tests. Existing project submission pages can preserve references, notes, reported output and invited-account human reviews. Expert-specific cases and objective implementation grading remain planned.

## How explanations should be written

1. Give the answer or behavior in one short sentence.
2. Explain why using ordinary words; define a technical term when it first matters.
3. Show a small example or walk through the example already in the question.
4. Explain the common mistake and how to avoid it.
5. Add an important limit only when it changes the answer.

Example: “Both names point to the same list. Adding an item through either name changes that one list. Assignment does not make a copy.” Introduce the word *alias* after this idea is clear.

Use JavaScript comparisons when they help this learner, but explain Python's rule directly. Keep advanced ideas accurate while using simple language. Simple wording should not turn a build-specific statement into a claim about every Python version.

## Build order and honest progress

- [x] Audit existing Python coverage and document the missing teaching path.
- [x] Provide beginner, intermediate and advanced knowledge tests.
- [x] Simplify all 72 Python answer explanations and the existing ownership lesson.
- [x] Author and verify the first nine-lesson foundations path with 18 scored scenarios and a local CLI starter.
- [x] Publish a five-lesson continuation covering text/bytes, collection patterns, dates/time and debugger workflows, with ten scenarios and a repair lab.
- [x] Publish five object-design/typing lessons, ten scored scenarios and a typed task-inbox project with runtime and static verification.
- [x] Publish five streaming/resource-cleanup lessons, ten scenarios and a service-log lab with lazy-reading and failure-path tests.
- [x] Publish eight packaging/HTTP lessons, 16 scenarios, an installable ingestion package with 28 offline tests, clean artifact verification and in-app manual review criteria.
- [x] Publish seven function/testing/logging/regex lessons, 14 scenarios and a separately packaged feed-policy lab with 49 public pytest cases and four manual criteria.
- [x] Publish eight async/work-limit lessons, 16 scenarios and a separate bounded HTTP-ingestion lab with 75 cases, typed installed selector composition and manual review criteria.
- [x] Publish and verify six advanced object-behavior lessons, 12 scenarios, complete guided/glossary/recall layers and a 50-case installable feed-object lab with four manual criteria.
- [x] Publish and verify seven advanced typing lessons, 14 scenarios, complete guided/glossary/recall layers and the installable transformation lab with 47 runtime cases and positive/ten rejected checker fixtures.
- [x] Publish and verify six context/resource lessons, twelve scenarios, complete guided/glossary/recall layers and the installable ownership lab with 54 public cases.
- [x] Publish and verify seven thread/process lessons, fourteen scenarios, complete guided/glossary/recall layers and a 66-case installed offload lab with actual process boundaries.
- [x] Publish and verify eight measurement/cache/compatibility lessons, sixteen scenarios, complete guided/glossary/recall layers and a 61-case installed lab with actual observations and compatible typed callers.
- [x] Publish and verify the first PostgreSQL persistence unit, complete learning layers, bounded installed lab and actual commit/rollback evidence.
- [x] Publish and verify eight ingestion-service lessons and seven competing-transaction lessons, sixteen scenarios, complete learning layers and a nineteen-file installed 70-case PostgreSQL/HTTP/migration lab with four manual criteria.
- [x] Publish and verify seven competing-transaction lessons, fourteen scenarios, complete learning layers and a thirteen-file installed 70-case extension with observed PostgreSQL waits/deadlocks/isolation/retry/reconciliation and four manual criteria.
- [x] Publish and verify six durable-outbox lessons, twelve scenarios and a fourteen-file installed 67-case extension with actual worker exits/replay and four manual criteria.
- [x] Deliver bounded durable recovery and the composed advanced practical-review project with fixed manual submissions (ADRs 0031/0035).
- [ ] Complete broader expert/production practice with real learner artifacts and independent review.
- [x] Implement artifact references, evidence notes, pinned rubrics, self/human review and revision history for all thirty-two current projects, including the composed advanced practical-review project. Automated implementation grading for these local packages remains outside the academy API.
- [x] Publish the bounded composed practical case study with runnable reproductions, actual profile observations and original-artifact reviewer guidance (ADR 0035).
- [ ] Extend expert case studies to broader production workloads/security and independent learner evidence.

A completed reading, a listed topic, and a passed test are different kinds of progress. Record them separately.

## First PostgreSQL persistence continuation

Eight lessons from /lessons/python-relational-keys through /lessons/python-persistence-contracts add sixteen original scenarios and complete guided/diagram/glossary/recall layers. The eleven-file starter has three unfinished functions and 57 public cases, including 25 cases that require actual PostgreSQL; offline skips are not persistence verification. A freshly installed reference on PostgreSQL 17 verifies parameter binding, complete key/value duplicates, real constraints, owned transactions, late rollback, separate observers, bounded reads and typed prior Record/Row/Snapshot integration. Four manual criteria preserve interpretation (ADR 0024). Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.

## First ingestion-service continuation

Eight lessons from `/lessons/python-http-api-contracts` through `/lessons/python-service-evidence` add sixteen scenarios and complete guided/diagram/glossary/recall layers. Simple explanations connect strict Pydantic input, FastAPI dependencies, namespace permissions, SQLAlchemy Engine/Session ownership, commit-before-success, Alembic migrations and scoped keyset pages. The nineteen-file starter has three unfinished functions and 70 public cases (43 offline; 27 require PostgreSQL). Installed reference evidence includes real rollback, constraints, pool release/exhaustion, migration key/value preservation, readiness, prior-package adaptation and a loopback HTTP server. Four criteria keep learner-reported and human judgment separate (ADR 0025). This bounded unit does not complete advanced/expert practice, concurrency, durable recovery or the full backend path.

## First competing-transaction continuation

Seven lessons at `/lessons/python-pg-snapshots` through `/lessons/python-competition-evidence` add fourteen scenarios and full guided/diagram/glossary/recall coverage. The thirteen-file starter extends the completed service with three unfinished functions, 70 public cases (53 offline/17 PostgreSQL-dependent) and four manual criteria. Installed evidence observes real waits, commit/rollback races, snapshots, 40001/40P01/55P03/57014, copied whole-transaction retry, scoped reconciliation and pool/setting cleanup. A modeled missing response after real commit is labeled, and actual in-flight absence is distinct from rollback. This bounded unit does not complete expert practice, durable recovery, load/fairness or the full backend path (ADR 0026).

## First durable outbox continuation

Six ordered lessons (python-outbox-atomicity through python-outbox-evidence), twelve scenarios and full learning layers connect the completed service/competition wheels to a fourteen-file 67-case extension. Three functions own fact/intent recording, one locked publication and inbox/effect consumption. Installed evidence includes three actual worker exits with committed state/replay, scoped claims, zero/revision keys, explicit adoption and one effect despite repeated delivery. Four manual criteria preserve interpretation. Bounded worker leases/fencing, saved retries/quarantine and cooperative shutdown are delivered in ADR 0028. Brokers, operations and applied AI remain open (ADR 0027).

## Leased worker continuation

Six ordered lessons (python-worker-leases through python-worker-evidence) add twelve original scenarios under Worker lease contracts, twelve guided choices/terms/private recall variants and six diagrams. The authenticated fourteen-file leased-worker extension has three unfinished functions and 59 public cases (35 offline/24 PostgreSQL-dependent), with four manual review criteria. Four freshly built/installed local packages on PostgreSQL 17.11 verify short committed leases, copied stable events, current-generation/live-deadline settlement, persisted retry times/attempt limits, poison/exhaustion quarantine, bounded admission, real acknowledgment rollback, two actual child exits/observed expiry/generation-2 reclaims and cooperative SIGTERM. Replay preserves one local consumer effect. Old Event/Accepted/service routes and permissions remain unchanged; reported output and checklists do not award mastery (ADR 0028).

## Broker delivery continuation

Six ordered lessons (python-event-envelopes through python-stream-evidence), twelve original scenarios under separate Stream delivery contracts, and complete guided/diagram/glossary/private recall layers connect to the Broker delivery lab. Its authenticated fifteen-file starter has three unfinished functions, 74 public cases (59 offline/15 live) and four manual criteria. Five fresh installed local packages verify strict supported v1/v2 envelopes with stable Event identity, checked Redis XADD/WAITAOF local AOF acceptance on one physical connection, producer completion before consumer effects, inbox/effect commit before XACK, pending/reclaim/cursor/deleted-gap semantics, duplicate/conflicting facts, real constraints, two actual child exits and a controlled retained-AOF broker restart. PostgreSQL 17.11, Redis 7.4.2 and redis-py 6.4.0 are observed; reported evidence does not award mastery (ADR 0029).


## Published delivery migration continuation

Six ordered lessons (python-delivery-revisions through python-migration-evidence), twelve original scenarios under separate Delivery migration contracts, and complete guided/diagram/glossary/private recall layers connect to the Delivery migration lab. Its authenticated sixteen-file starter has three unfinished functions, 44 public cases (25 offline/19 live) and four manual criteria. Six freshly built/installed packages on PostgreSQL 17.11 verify an unchanged service_001/002 plus delivery_003/004 chain, all-field/timestamp preservation without implicit enqueue, combined metadata/head/autogenerate comparison, actual late upgrade/downgrade rollback, cooperating advisory locks/real DDL timeout, explicit destructive targets and retained facts versus lost delivery history. Actual Redis composition preserves prior contracts; old service /ready intentionally reports 503 at the new head. Re-upgrade has empty inbox history and can apply the same key again. Finite reported evidence does not award mastery (ADR 0030).

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.


## Delivery retention and explicit redrive

Four ordered lessons (python-dead-job-inspection through python-recovery-evidence), eight original scenarios under separate Delivery recovery contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery recovery lab. Its authenticated twelve-file starter has three unfinished functions, 36 public cases (14 offline/22 live) and four manual criteria. Seven installed packages on owned PostgreSQL/Redis verify bounded inspection, one concurrent redrive success, preserved Event/generation/policy, exhausted refusal, stale-lease refusal, local rollback, atomic current-group payload checks and duplicate-safe replay with all local history retained. Payload deletion can survive later call failure. Reported evidence does not award mastery (ADR 0031).


## Installed release operation coverage

Four ordered lessons (python-release-settings through python-release-evidence), eight original scenarios under Release operating contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery release lab. Its authenticated fourteen-file starter has three unfinished functions, 33 public cases (15 offline/18 live) and four manual criteria. Eight installed packages on owned PostgreSQL/Redis verify private copied settings, compatible delivery_004 readiness, preserved business contracts, real failures, one owned disposal, installed operating commands/loopback SIGTERM cleanup and exact rollback losses with re-upgrade. Reported evidence does not award mastery (ADR 0032).

The current release unit teaches environment/JSON ownership, immutable copies, generic errors, FastAPI mounting/lifespan, PostgreSQL read-only query probes, explicit Alembic checks, Uvicorn loopback shutdown and destructive rollback decisions. Full operations/backup/zero-downtime and expert practical certification remain open. Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.


## Delivered SQL query depth and plans

Five ordered lessons (python-query-joins through python-query-evidence), ten original scenarios under SQL query analysis contracts and complete guided/diagram/glossary/private recall layers connect to the SQL query analysis lab. Its authenticated nineteen-file starter has three unfinished SQL queries, 36 public cases (23 offline/13 PostgreSQL) and four manual criteria. Nine installed packages verify complete-key/fanout/empty reports, zero-safe revision windows, newest-before-JSONB filtering, read-only owned queries, source compatibility and actual result-equivalent baseline/indexed plans on 40,000 records/notes. Five literal lesson SQL examples also run on PostgreSQL. Reported evidence does not award mastery (ADR 0033).

The query continuation connects Python typed boundaries to complete relational keys, explicit frames, JSONB operator semantics and measured plans. The original 72-question Python evaluations remain unchanged; neither finite queries nor knowledge scores certify expertise. Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.


## Delivered API depth

Five ordered lessons (python-http-validators through python-api-depth-evidence), ten original scenarios under separate API delivery contracts and complete guided/diagram/glossary/private recall layers connect to the API depth lab. Its authenticated fourteen-file starter has three unfinished functions, 51 public cases (39 offline/12 PostgreSQL) and four manual criteria. Nine freshly installed packages verify private conditional GET/permission ordering, framed raw-byte HMAC/freshness/strict events, atomic scoped receipts/readings, real competing duplicates/conflicts/rollback/lock timeout and compatible prior routes. The saved actual loopback HTTP report observes 200/304/change, 401/403/409/422/503/retry, committed counts and released connections. Reported tests and manual review do not award mastery (ADR 0034).

The API continuation connects hmac/hashlib/json, raw Request streaming, configured route authority, SQLAlchemy/PostgreSQL transactions, pytest and actual HTTPX/Uvicorn requests. Standard-library examples explain one idea at a time; installed requests/store cases evaluate practical boundaries. The composed practical-review project is delivered in ADR 0035, with original artifacts and self/human feedback kept separate from mastery. Python knowledge exams remain the original 72 questions; expert certification is not claimed.


## Composed advanced Python practical review

Five lessons (`python-practical-contracts` through `python-practical-review`), ten original scenarios and complete guided/diagram/glossary/private recall layers connect to the Composed Python practical review lab. Its authenticated eighteen-file starter has three unfinished functions, 50 public cases (47 offline/three PostgreSQL) and four manual criteria covering all seven advanced review dimensions. Eight freshly installed local packages compose strict old service pages, latest/conflict/domain adapters, immutable typed snapshots, response/resource ownership, bounded cache and actual thread/spawn workers. A stated 128-fact workload gives equivalent reporting outputs with 152/32 computations and 120 hits; a cyclic case gives 64/64 and zero hits. Actual cProfile call counts, raw wall/CPU intervals and Python allocation observations have no speed threshold. The original-case/regression/design task feeds fixed manual submissions and revisions. Maintainer fixtures and reported tests never establish learner originality, mastery or expertise (ADR 0035).

Learn this unit after API depth. The standard library supplies cProfile/pstats/tracemalloc, hashing, dataclasses, context/resource helpers and thread/process machinery; HTTPX, FastAPI/Pydantic, SQLAlchemy/Psycopg 2 and Alembic provide the selected service boundaries. Pytest/mypy/build/Ruff are development tools. No new academy runtime dependency is introduced.

| Lesson | Focus |
| --- | --- |
| python-practical-contracts | Strict copied pages, conflicts/latest selection and old value domains. |
| python-practical-lifetimes | Borrowed clients, owned response/server/files and actual worker cleanup. |
| python-practical-profiling | Equivalent outputs before raw timing/profile/allocation observations. |
| python-practical-compatibility | Old service, typed values and deprecated caller boundaries. |
| python-practical-review | Original case/regression/design artifact, fixed submissions and manual revisions. |


## Offline model contracts

Six lessons (`model-request-contracts` through `model-contract-evidence`), twelve original scenarios under separate **Model call contracts** and complete guided/diagram/glossary/private recall layers connect to the Model contracts lab. Its authenticated fourteen-file starter has three unfinished functions, **84 offline public cases** and four manual criteria. A clean installed standard-library package normalizes two invented provider formats; checks pinned model/prompt/schema, copied complete-envelope context/output admission, strict complete/refused/incomplete proposal/usage variants; and reserves fictional credits before attempts, settles only valid usage, retains unknown reserves and stops at cost/step/one cooperative deadline boundaries. Actual waiting fixtures verify timeout cleanup and propagated external cancellation. Installed JSON records eleven finite cases without raw prompts/refusal reasons/exceptions. No real model, network, current pricing, provider conformance or semantic quality is claimed (ADR 0036).

Python remains 152 lessons/304 scenarios and the original 72 evaluation questions. This applied AI unit adds standard-library asyncio, Protocol, dataclasses and strict JSON application practice in the LLM track. Its 84-case installed project requires no third-party runtime provider SDK; pytest/mypy/build/Ruff are development tools.


## Scoped embeddings and retrieval

Six lessons (`retrieval-chunk-identities` through `retrieval-evidence`), twelve original scenarios under separate **Scoped retrieval contracts** and complete guided/diagram/glossary/private recall layers connect to the Scoped retrieval lab. Its authenticated fifteen-file starter has three unfinished functions, **83 public cases** and four manual criteria. The installed standard-library package preserves complete chunk keys/character offsets/digests, validates model/version/dimensions/finite nonzero vectors, chooses latest revisions before trusted tenant/group/activity/metadata filters, then computes exact cosine or simple ASCII token-set Jaccard ranking with full-key ties. Requested-k precision, labelled recall and first-relevant rank use explicit denominators; no-label cases have null recall/rank and separate unwanted-hit counts. Four computed reports use an original 12-revision/15-chunk/nine-query development fixture with hand-supplied six-dimensional vectors. No real embedding model, ANN/database index, held-out quality, durable document lifecycle or automatic mastery is claimed (ADR 0037).


## Verified RAG continuation (2026-10-11)

Six simple lessons (`rag-source-lifecycle` through `rag-practical-evidence`), twelve original scenarios under separate **Evidence answering contracts** and complete guided/diagram/glossary/private recall layers connect to the Evidence answering lab. Its authenticated fifteen-file starter has three unfinished functions, **70 public cases** and four manual criteria. The installed `academy-rag-lab==0.1.0` composes the published model and retrieval packages. A separate local SQLite index atomically publishes complete revisions, retains deletion markers and rejects older/conflicting publication. Trusted access filters, a stated task-term gate, keyword reranking and whole-passage UTF-8 packing select evidence before a bounded controlled call. Exact selected excerpts become citations only after current permissions, source identity and index epoch are rechecked. Missing evidence, invalid output and stale authority return no answer text. Seventeen computed experiments observe lifecycle, refusal, invalid proposals, admission, cancellation and freshness. Controlled quotes and hand-assigned vectors do not evaluate semantic answer quality or production authorization; manual submissions never award mastery (ADR 0038).

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.


## Verified tool-use continuation (2026-10-11)

Six simple lessons (`tools-proposal-boundaries` through `tools-practical-evidence`), twelve original scenarios under separate **Authorized tool contracts** and complete guided/diagram/glossary/private recall layers connect to the Authorized local tools lab. Its authenticated fifteen-file starter has three unfinished functions, **81 public cases** and four manual criteria. The installed `academy-tools-lab==0.1.0` composes model, retrieval and RAG packages. Strict proposals cannot grant authority; current application actor/principal/source checks and exact action approval precede effects. One local transaction commits a note and its scoped receipt under a stable application operation ID independent of model call IDs. Same actions replay, changed actions conflict, caps and late SQL failures are observed. One cooperative whole-loop deadline and context/cost/step budgets stop uncertain outcomes without automatic effect retries. Seventeen computed experiments observe actual calls, notes/receipts, lost-result reconciliation and cancellation; public reports redact source text and pin provider/model/prompt/schema. Controlled local evidence is not real model quality, production authority or distributed exactly-once; manual submissions never award mastery (ADR 0039).

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.


## Verified final step-six evaluation and path audit (2026-10-12)

Six simple lessons (`ai-release-cases` through `ai-release-review`), twelve original scenarios under separate **AI release evidence** and complete guided/diagram/glossary/private recall layers connect to the Controlled AI release evaluation lab. Its authenticated fifteen-file starter has three unfinished functions, **54 public cases** and four manual criteria. Five installed packages execute eighteen versioned development cases for each of two candidates: **36 actual observations**. Requested-k precision is **1/4** and positive-label recall/MRR **1/2**; raw cosine has **one** unlabelled unwanted hit and the stated task-term gate has **zero**. Exact answer/tool contracts, permission/privacy/boundary counts, dataset/candidate digests and inclusive rational thresholds remain separate from two pending semantic reviews. Reports redact raw contents; role/URL/extra-field, stale-source and post-commit timeout paths are observed. The separately labelled mutation demonstrates evaluator rejection rather than claiming another provider run. Controlled development data and hand vectors do not establish real model quality or production security (ADR 0040).

The agreed nine-milestone teaching/lab sequence is complete. [Coverage audit](COVERAGE_AUDIT.md) records the actual boundaries; broader product/portfolio/reliability work remains planned.

Step seven is complete within the scope in STEP_7_PORTFOLIO_EXAMS.md. Wait for the user to continue before starting step eight. Then verify the complete Docker/PostgreSQL topology first; implement and verify backup/restore, account recovery, evidence exports, accessibility and mobile acceptance, recording real observations and preserving learner state. Do not infer production readiness from the isolated runner or from portfolio checklists.
