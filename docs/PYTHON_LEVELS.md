# Python levels and library guide

For the full teaching plan and an honest account of missing lessons, see [Python learning path](PYTHON_LEARNING_PATH.md). The tests below sample knowledge; the complete beginner-to-expert course has not been built yet.

Dedicated beginner, intermediate and advanced Python knowledge evaluations are available in Assessments. The original mixed engineering diagnostic remains available separately. These tests do not imply that the full Python curriculum or practical grading workflow is complete.

A level is demonstrated by reasoning and implementation, not by collecting package names. Know how to use documentation; memorizing every API is not required. These lists are the academy’s recommended scope, not universal certification standards. Tests target Python 3.13+ and never execute learner code.

## Beginner
20 questions, approximately 35 minutes (untimed). Categories: Values & expressions, Collections, Control flow, Functions & errors, Files & modules.

These are working-proficiency targets for this academy, not a universal list required by every employer. Built-ins are language fundamentals; the standard library ships with Python. Third-party packages and tools are labeled separately. The test samples knowledge and does not assess every library listed.

| Library / tool | Scope | Expected ability |
| --- | --- | --- |
| [pathlib](https://docs.python.org/3/library/pathlib.html) | Core standard library | Build paths, read/write text with explicit encoding, and handle missing files. |
| [json and csv](https://docs.python.org/3/library/json.html) | Core standard library | Parse and write interchange files; distinguish serialization from data validation. |
| [datetime and time](https://docs.python.org/3/library/datetime.html) | Core standard library | Parse/format basic dates and durations; distinguish elapsed time from calendar time. |
| [math and random](https://docs.python.org/3/library/math.html) | Core standard library | Use common numeric helpers and reproducible non-security randomness; do not use random for secrets. |
| [os and sys](https://docs.python.org/3/library/os.html) | Core standard library | Read environment variables and arguments; understand interpreter and process boundaries. |
| [venv and python -m pip](https://docs.python.org/3/library/venv.html) | Environment tools | Create a project environment and install packages into the correct interpreter. pip is a package-management tool, not an imported application library. |
| [unittest or pytest](https://docs.python.org/3/library/unittest.html) | Testing choice | Write small success, boundary and failure tests. unittest is built in; pytest is an optional third-party alternative. |
| [HTTPX or Requests](https://www.python-httpx.org/quickstart/) | Optional integration practice | Try one HTTP client after fundamentals: status handling, JSON, and explicit timeouts. Neither is required to qualify as a Python beginner. |

### Practical follow-up (not automatically graded)
Build a CLI that reads a CSV of expenses, validates amounts, groups by category, writes a JSON summary and tests invalid/missing input. Review the code and tests manually; this test does not execute or grade that project.

## Intermediate
24 questions, approximately 55 minutes (untimed). Categories: Functions & scope, Objects & types, Iteration & resources, Reliability & standard library, Async & concurrency, Testing & packages.

These are working-proficiency targets for this academy, not a universal list required by every employer. Built-ins are language fundamentals; the standard library ships with Python. Third-party packages and tools are labeled separately. The test samples knowledge and does not assess every library listed.

| Library / tool | Scope | Expected ability |
| --- | --- | --- |
| [collections and collections.abc](https://docs.python.org/3/library/collections.html) | Core standard library | Choose Counter/defaultdict/deque and reason about collection interfaces and shared state. |
| [itertools and functools](https://docs.python.org/3/library/itertools.html) | Core standard library | Build lazy pipelines, understand adjacent groupby, use wraps and justify bounded caching. |
| [dataclasses, enum and copy](https://docs.python.org/3/library/dataclasses.html) | Core standard library | Model value objects, use default_factory, distinguish shallow/deep copying and mutation ownership. |
| [typing](https://docs.python.org/3/library/typing.html) | Core standard library | Annotate collections and unions; understand generics and basic Protocol usage, static checking versus runtime validation. |
| [contextlib](https://docs.python.org/3/library/contextlib.html) | Core standard library | Manage resources with context managers, finally and explicit exception propagation. |
| [logging](https://docs.python.org/3/library/logging.html) | Core standard library | Use levels, named loggers, tracebacks and safe correlation fields; avoid leaking secrets. |
| [datetime, zoneinfo and decimal](https://docs.python.org/3/library/zoneinfo.html) | Core standard library | Distinguish instants/local schedules, use time zones deliberately and implement explicit decimal rounding policies. |
| [pathlib, tempfile and shutil](https://docs.python.org/3/library/tempfile.html) | Core standard library | Stream files, clean temporary resources, and reason about partial writes and file operations. |
| [re and argparse](https://docs.python.org/3/library/argparse.html) | Core standard library | Use focused patterns and named groups, and create CLI contracts with validation and help. |
| [asyncio and concurrent.futures](https://docs.python.org/3/library/asyncio.html) | Core for this backend path | Await/schedule work, bound concurrency, handle cancellation and select threads versus processes based on the workload and interpreter. |
| [unittest.mock; pytest](https://docs.pytest.org/en/stable/) | Testing practice | Patch the lookup site, use fixtures/parametrization, and test failures without mocking the behavior under test. pytest is the recommended third-party test runner for this path. |
| [sqlite3 and secrets](https://docs.python.org/3/library/sqlite3.html) | Useful standard-library boundaries | Bind SQL parameters and understand transactions; generate security tokens with secrets rather than random. |
| [HTTPX](https://www.python-httpx.org/) | Backend integration recommendation | Use a managed client, timeouts, status/error handling and async clients when appropriate. Requests is a sync alternative; learning both is not a gate. |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/models/) | Backend boundary recommendation | Validate external input with models, understand coercion/strictness, and keep authorization in application logic. |
| [FastAPI or Django/DRF; SQLAlchemy, Alembic and psycopg](https://fastapi.tiangolo.com/) | Next backend specialization | Learn a framework and database stack through a project. These are domain skills, not prerequisites for general intermediate Python. |
| [Hypothesis](https://hypothesis.readthedocs.io/en/latest/) | Optional testing depth | Explore invariants with property-based tests after mastering example-based tests. |
| [NumPy, pandas, scikit-learn, PyTorch, provider SDKs](https://numpy.org/doc/stable/) | Optional data/AI specialization | Add only for the chosen project. Tensor frameworks, data libraries and orchestration frameworks are not general Python level requirements. |
| [Ruff; mypy or Pyright; pip/uv and pyproject.toml](https://packaging.python.org/en/latest/tutorials/packaging-projects/) | Development tools | Run lint/format and static checks; declare and reproduce package dependencies. Tools support proficiency but are not imported runtime libraries. |

### Practical follow-up (not automatically graded)
Build an installable ingestion package with typed boundaries, streaming parsing, managed HTTP clients, bounded concurrency, explicit cancellation/errors, and tests using fakes. Add regression cases for duplicate input and malformed records. Review the implementation separately; this knowledge score does not certify it.

The synchronous portion is now published at `/lessons/python-packages` through `/lessons/python-ingestion-tests`, with an installable project in Projects. Its 28 public tests cover strict parsing, HTTP response ownership and failures; types/lint and clean wheel/source-archive installation are verified separately. Bounded async concurrency/cancellation is published separately; the first persistence/deduplication and service units are published separately; competing transactions, recovery and the full service remain planned. Runtime library: HTTPX 0.28.1. Standard-library work: json, re, dataclasses, collections.abc, contextlib, importlib.resources, argparse, urllib.parse, unittest and unittest.mock. Workflow tools: venv/pip, build/setuptools/wheel, mypy and Ruff. Tool names are not mastery evidence.

## Interpreting results
Each question has equal weight. The provisional target is at least 80% overall and at least 60% in each topic. A weak category can therefore prevent meeting the target despite a high total. Scores are shown with correct/total counts. Review explanations and linked official reading after submission. Retakes use the same bank and can reflect memorization; they are practice, not independent certification. These results do not inflate the existing mastery score.

## Advanced

28 questions, approximately 75 minutes (untimed). Assumes intermediate fluency. Each of seven topics has four questions: object model/protocols, typing/API contracts, resource lifetime/isolation, async failure/cancellation, concurrency/process boundaries, performance/memory, and packaging/verification. Python 3.13+ is the baseline; questions identify implementation-specific assumptions such as a GIL-enabled CPython build.

These are working-proficiency targets for this academy, not a universal list required by every employer. Built-ins are language fundamentals; the standard library ships with Python. Third-party packages and tools are labeled separately. The test samples knowledge and does not assess every library listed. Build on the beginner and intermediate libraries above.

| Library / tool | Scope | Expected ability |
| --- | --- | --- |
| [typing](https://docs.python.org/3.13/library/typing.html) | Core standard library | Use ParamSpec, TypeVar, Protocol and variance deliberately; distinguish static assumptions from runtime validation. |
| [contextlib and contextvars](https://docs.python.org/3.13/library/contextlib.html) | Core standard library | Manage dynamic sync/async cleanup and scoped context bindings; reason about propagation and restoration. |
| [asyncio](https://docs.python.org/3.13/library/asyncio-task.html) | Core for this backend path | Design structured task lifetimes, cancellation, timeouts and bounded producer/consumer flows. |
| [concurrent.futures, multiprocessing and threading](https://docs.python.org/3.13/library/concurrent.futures.html) | Core concurrency boundaries | Choose execution models with measured costs, resource ownership, serialization and shutdown contracts. |
| [functools and weakref](https://docs.python.org/3.13/library/functools.html) | Core lifetime reasoning | Understand cache retention, invalidation, decorator metadata and when weak references are appropriate. |
| [cProfile, pstats, timeit and tracemalloc](https://docs.python.org/3.13/library/profile.html) | Standard-library measurement tools | Profile representative CPU workloads and Python allocations; explain limits of microbenchmarks and RSS attribution. |
| [importlib.resources and importlib.metadata](https://docs.python.org/3.13/library/importlib.resources.html) | Core packaging boundaries | Load package resources and distribution metadata without assumptions about the working directory. |
| [pytest, unittest.mock and Hypothesis](https://docs.pytest.org/en/stable/) | Testing recommendation | Test failure paths with controlled fakes and clocks; use property-based tests for invariants when useful. Hypothesis is optional. |
| [build, pip/uv, Ruff and mypy/Pyright](https://packaging.python.org/en/latest/tutorials/packaging-projects/) | Development tools | Verify built artifacts in clean environments, reproduce dependencies and run lint plus static checks. These are tools, not runtime proficiency gates. |
| [HTTPX, Pydantic, SQLAlchemy and Alembic](https://www.python-httpx.org/advanced/clients/) | Backend specialization | Apply connection/session lifetimes, validated boundaries and migration discipline in realistic projects. Framework knowledge alone does not establish advanced Python skill. |

### Practical review (implemented manual workflow)
The [Composed Python practical review lab](../content/projects/practical-review/starter/README.md) connects the earlier libraries and PostgreSQL service to an installed report with actual HTTP reads, equivalent baseline/cache outputs, cProfile and Python allocation observations, bounded thread/process workers and old caller checks. Begin at `/lessons/python-practical-contracts`. Complete the three learner functions, then create your own [case, regression and decision note](../content/projects/practical-review/starter/REVIEW_TASK.md). Include built-wheel versions, exact revision/commands and actual report/test output.

Submit through `/projects/python-practical-review`: saved drafts, fixed submitted artifact/rubric versions, self/human feedback, revocable reviewer access and revisions are implemented. Four in-app criteria group the seven dimensions below: object/type/caller compatibility; resource/async ownership; bounded work/process boundaries; profile/install/original artifact. Reviewers record **demonstrated**, **needs work**, or **not reviewed** with concrete evidence. The data-only case helper checks expected outputs/counts, while originality, adequacy and tradeoffs need manual judgment. Test reports and manual submissions do not automatically award mastery or certify expertise.

| Review criterion | Evidence to inspect |
| --- | --- |
| Object and typing contracts | A typed extension protocol, static-check output and tests for invalid external input; explain ownership and mutation rules. |
| Resource safety | Failure injection after partial acquisition; evidence that opened resources close and unrelated exceptions propagate. |
| Task lifetime | Deterministic cancellation/failure tests showing child cleanup and shutdown, including uncertain effects from blocking work. |
| Bounded work | Queue/worker/pending/cache limits and actual bounded execution; explain why finite traces do not prove arbitrary sustained-load safety. |
| Process boundaries | Importable worker entry points, serializable payloads and process-owned resources; justify the chosen execution model. |
| Performance analysis | Reproducible workload, profile and memory observations, before/after measurements and stated measurement limits. |
| Distribution and reliability | Install the built wheel outside the checkout; verify resources, dependency support and retry/idempotency failure cases. |

The knowledge target remains 80% overall and 60% per topic: with this bank, at least 23/28 overall and 3/4 in each topic. Practical evidence should be assessed separately, even when the knowledge target is met. Retakes reuse the bank.

## Published intermediate function/testing tools

The seven-lesson unit at `/lessons/python-closures` uses standard-library `functools`, `inspect`, `logging` and `re`, plus pytest for test design. Its runtime needs no third-party package. The lab pins pytest 9.0.3, mypy 2.3.1, Ruff 0.16.7 and build 1.2.2.post1 as development tools. Learn fixtures, yield cleanup, parametrization, monkeypatch and caplog through behavior tests. Passing 49 bounded cases demonstrates that contract, not complete intermediate or expert knowledge. Bounded async tools are now published separately; advanced typing is now published separately.

## Published async tools and work limits

The eight-lesson unit at `/lessons/python-coroutines` uses standard-library `asyncio`, `contextlib` and asynchronous interfaces from `collections.abc`. Learn TaskGroup, timeout, Event, bounded Queue, async iteration, aclosing and AsyncExitStack through explicit ownership. HTTPX 0.28.1 supplies AsyncClient and deterministic MockTransport/AsyncByteStream tests. Pytest 9.0.3 runs local tests through standard-library event loops; no pytest-asyncio plugin is required for this lab. Mypy, Ruff and build remain development tools. The 75 cases demonstrate bounded local behavior, not full advanced Python or production concurrency expertise. Object behavior and advanced typing are now published separately; advanced contexts are published separately; threads/processes/build differences are published separately; measured performance is published separately; the bounded service and composed practical-review units are published; broader expert/production evidence remains open.

## Published advanced object tools

The six lessons at `/lessons/python-attribute-lookup` through `/lessons/python-object-contracts` use Python's built-in object rules plus standard-library `inspect` (getattr_static), `dataclasses`, `collections.abc` (Sequence/Iterable), `types` (NotImplementedType), `typing` (overload) and focused `re` validation. Understand default descriptor priority, __set_name__, per-owner state, receiver MRO/super, type-based implicit operations, stable equality/hash fields and shallow versus element immutability. No third-party runtime library is necessary for this unit. Pytest 9.0.3, mypy 2.3.1, Ruff 0.16.7 and build 1.2.2.post1 are development tools. The 50-case package and four manual criteria are bounded evidence. Advanced typing/generics is now published separately; contexts are published separately; threads/processes and profiling/cache/library evolution are published; the composed practical review is delivered in ADR 0035; broader expert case studies remain open.

## Published advanced typing tools

The seven lessons from `/lessons/python-generic-functions` through `/lessons/python-typed-interfaces` use standard-library `typing` (TypeVar, ParamSpec, Protocol, overload, TypeGuard, TypeIs, TypedDict, cast, NewType and assert_type), `collections.abc`, `functools`, `dataclasses` and bounded `re` validation. Learn modern generic syntax alongside traditional explicit variables, producer/consumer variance, preserved call shapes and honest narrowing. The lab has no third-party runtime dependency. Mypy 2.3.1, pytest 9.0.3, Ruff 0.16.7 and build 1.2.2.post1 are pinned development tools. Runtime checks and one positive/ten rejected checker fixtures establish separate finite evidence; neither typing tool choice nor a green result proves expertise. Context/resource lifetime is published separately; thread/process concurrency is published separately; measurement/library evolution is published separately; full expert cases remain planned. typing_extensions is a compatibility backport when supporting older interpreters, not needed for this 3.13+ lab.

## Published advanced resource tools

Six lessons from /lessons/python-exit-stack through /lessons/python-resource-contracts use standard-library contextlib (ExitStack, AsyncExitStack, contextmanager, asynccontextmanager), contextvars (ContextVar, tokens, copy_context), weakref, asyncio and gc for known collectible test fixtures. Learn immediate handoff, non-suppressing callbacks versus exits, native chains, awaited cooperative release, shallow task context and single weak lookup. There is no third-party runtime dependency. Pytest 9.0.3, mypy 2.3.1, Ruff 0.16.7 and build 1.2.2.post1 are development tools. Fifty-four finite cases and manual criteria do not certify expertise. Thread/process concurrency is published separately; measurement/library evolution is published separately; the first persistence unit is published; the first service integration is published; the first competing-transaction/retry/reconciliation unit is published; the first outbox/process-replay unit is published; leases/backoff/shutdown and broader recovery remain next.

## Published thread/process tools

Seven lessons from /lessons/python-thread-process through /lessons/python-offload-contracts use standard-library concurrent.futures (Executor, Future, ThreadPoolExecutor, ProcessPoolExecutor), threading (Lock, Event), multiprocessing (explicit spawn contexts), collections.deque, itertools.islice, pathlib, tempfile, dataclasses, os, sys/sysconfig and platform. Learn outstanding admission, ordered latency, queued-only cancellation, wait-only timeouts, joined ownership, top-level serializable workers and worker-local handles. Locks protect cooperating invariants, including readers; build/version/runtime GIL facts stay distinct. These are runtime modules, not packages to install.

The local lab needs no third-party runtime dependency. Pytest 9.0.3, mypy 2.3.1, Ruff 0.16.7 and build 1.2.2.post1 are development tools; setuptools 83.0.0/wheel 0.48.0 build artifacts. Sixty-six finite cases, actual process PIDs and clean installed composition show the stated contract, without proving universal thread safety, speedup or expertise. Measured profiling/memory/cache/library evolution is published separately. The first PostgreSQL persistence unit is published; the first service integration is published; the first competing-transaction/retry/reconciliation unit is published; the first outbox/process-replay unit is published; leases/backoff/shutdown and broader recovery remain next.

## Published measurement/cache/compatibility tools

Eight lessons from /lessons/python-measurement-baselines through /lessons/python-measurement-contracts use standard-library time (perf_counter_ns/process_time_ns), timeit, cProfile/pstats, tracemalloc, sys.getsizeof, functools.lru_cache, collections.OrderedDict, dataclasses, warnings, pathlib and platform. Learn comparable workload/state/order, raw samples, self versus cumulative cost, input growth/materialization, traced current/peak/snapshots versus RSS/native/deep graph memory, complete cache keys, explicit eviction/reference release and compatible deprecated callers. Modules are runtime tools, not extra packages to install.

The lab has no third-party runtime dependency. Pytest 9.0.3, mypy 2.3.1, Ruff 0.16.7 and build 1.2.2.post1 are development tools; setuptools 83.0.0/wheel 0.48.0 build artifacts. Sixty-one finite cases and installed compatible callers inspect behavior separately from actual measurement JSON and manual interpretation. No fixed speedup/byte gate, automatic freshness, thread safety or expertise is claimed. The first PostgreSQL persistence unit is published; the first FastAPI/SQLAlchemy/Alembic unit is published; the first bounded competition unit is published; durable recovery and full expert project evidence remain later work.

## Published PostgreSQL persistence tools

Eight lessons from /lessons/python-relational-keys through /lessons/python-persistence-contracts use PostgreSQL 17 SQL constraints/transactions/ON CONFLICT/ORDER BY/LIMIT and Psycopg 2 value binding, cursor/connection contexts, transaction state and sql.Identifier. Learn row identity, parent references, required/range rules, caller versus transaction ownership, aborted/uncertain outcomes, exact repeat versus conflicting facts and complete bounded reads. The lab runtime pins psycopg2-binary 2.9.10, matching the academy driver; driver choice and production installation remain contextual.

Development tools include types-psycopg2 2.9.21.20260911 (checker stubs), pytest 9.0.3, mypy 2.3.1, Ruff 0.16.7 and build 1.2.2.post1, with setuptools 83.0.0/wheel 0.48.0. The reference passes 57 finite public cases on PostgreSQL and installed earlier-package composition; four criteria keep evidence manual. The first SQLAlchemy/Alembic/FastAPI service unit and bounded pooling/failure evidence are published separately. Indexes/query plans, competing transactions/retries, workers/backups and full service/expert practice remain later work. A module/tool list does not certify expertise.

## Published ingestion-service libraries

Eight lessons from `/lessons/python-http-api-contracts` through `/lessons/python-service-evidence` teach the first service built on the earlier Python/PostgreSQL contracts. These are backend specialization skills, not universal Python-level gates.

| Library / tool | Role in this unit | Learn by doing |
| --- | --- | --- |
| FastAPI 0.141.1 and Starlette 1.6.0 | Third-party HTTP runtime | Route explicit input/output, authorize dependencies before opening resources, distinguish handled errors and liveness/readiness. |
| Pydantic 2.13.5 | Third-party boundary validation | Reject coercion/extra fields, understand shallow frozen models and select public response fields. Validation does not grant permission. |
| SQLAlchemy 2.0.43 | Third-party database runtime | Separate Engine, Connection and Session; own one explicit transaction, bind values, commit before success and release pooled resources. |
| Alembic 1.16.5 | Third-party migration workflow | Install packaged revisions explicitly, review drift, rehearse upgrade/downgrade and identify metadata loss. ORM models do not create schema automatically. |
| psycopg2-binary 2.9.10 and PostgreSQL 17 | Driver and external database | Observe actual constraints, commit/rollback and separate-reader visibility. Production driver/TLS choices need their own evidence. |
| HTTPX 0.28.1 and Uvicorn 0.35.0 | Local test/server tools | Separate in-process ASGI tests from a real loopback TCP server. Neither demonstrates TLS/proxy behavior. |
| hmac, secrets, logging, uuid, contextlib, dataclasses, importlib.resources and argparse | Standard-library runtime/tools | Generate private local tokens, compare safely, record selected correlation fields and manage explicit resource/setup scopes. |
| pytest 9.0.3, mypy 2.3.1, types-psycopg2 2.9.21.20260911, Ruff 0.16.7 and build 1.2.2.post1 | Development checks | Verify behavior, static relationships, lint and what a fresh environment installs. Stubs do not execute validation. |

The installed reference passes 70 finite public cases on PostgreSQL and preserves earlier package contracts. Four manual criteria require actual output and interpretation. This does not establish expertise, competing-writer stress, an automatic retry policy, durable worker recovery or public deployment.

## Published competing-transaction tools

Seven lessons from `/lessons/python-pg-snapshots` use the completed FastAPI/Pydantic/SQLAlchemy/Alembic/Psycopg service, PostgreSQL 17 snapshots/locks/SQLSTATE and standard-library concurrent.futures, threading (Event/Barrier/Lock), time, dataclasses, enum, collections.abc and unittest.mock. Learn separate-owner coordination, observed pg_blocking_pids, READ COMMITTED/REPEATABLE READ/SERIALIZABLE boundaries, local server limits and new transaction ownership.

The extension runtime depends on the completed local academy-ingestion-service-lab 0.1.0 wheel; install that first, since these lab distributions are not published on PyPI. No new academy runtime dependency is needed. Pytest 9.0.3, mypy 2.3.1, driver stubs 2.9.21.20260911, Ruff 0.16.7, build 1.2.2.post1 and HTTPX 0.28.1 support tests/installed evidence; setuptools 83.0.0/wheel 0.48.0 build artifacts. Real finite concurrency observations and 70 cases are separate from modeled response loss, manual judgment and expertise. Durable worker/outbox/recovery, broader database/HTTP depth and applied AI remain open.

## Published outbox and worker tools

Six lessons from `/lessons/python-outbox-atomicity` use PostgreSQL 17 transactions/ON CONFLICT/SKIP LOCKED, SQLAlchemy Engine/Session ownership and the prior FastAPI/Psycopg service. Standard-library dataclasses, collections.abc, subprocess, os._exit, threading.Event, concurrent.futures, time and pathlib support bounded values and observed worker exits. Learn stable event identity, independent producer/consumer commits and actual database state rather than memorizing library names.

The local extension depends on completed service/competition 0.1.0 wheels and adds no academy runtime package. Existing pytest/mypy/driver-stubs/Ruff/build/HTTPX/setuptools/wheel pins support development/installed evidence. A PostgreSQL inbox protects the demonstrated local aggregate effect; real brokers/external effects, leases/fencing, retry scheduling and shutdown still need practice. Reading, finite tests and manual review do not certify expertise.

Advanced/backend worker practice now includes the six leased-worker lessons and installed 59-case lab for reservations, stale settlement, saved retries/quarantine and cooperative SIGTERM (ADR 0028). This extends finite practical evidence; it does not make the knowledge evaluation or curriculum an expert certificate.

For backend worker practice, the Redis Streams unit uses redis-py 6.4.0 with the existing SQLAlchemy/psycopg2/Alembic packages, standard-library JSON/subprocess helpers and pytest/mypy/build tools. These are role-specific tools, not a claim that every Python expert must know every library. Six simple lessons and the 74-case installed lab evaluate versioned envelopes, explicit broker acceptance and local duplicate-safe effects (ADR 0029).


## Delivery migration library practice

The six migration lessons and sixteen-file lab use the already chosen Alembic 1.16.5/SQLAlchemy 2.0.43/Psycopg 2.9.10 stack and the completed local delivery packages; redis-py 6.4.0 remains transitive for real composition. Standard-library work includes importlib.resources, contextlib, dataclasses and io. Learn immutable revision resources, explicit connection ownership, complete data preservation, drift-check scope and destructive-history boundaries through a project; package names alone do not establish advanced proficiency.

Six ordered lessons (python-delivery-revisions through python-migration-evidence), twelve original scenarios under separate Delivery migration contracts, and complete guided/diagram/glossary/private recall layers connect to the Delivery migration lab. Its authenticated sixteen-file starter has three unfinished functions, 44 public cases (25 offline/19 live) and four manual criteria. Six freshly built/installed packages on PostgreSQL 17.11 verify an unchanged service_001/002 plus delivery_003/004 chain, all-field/timestamp preservation without implicit enqueue, combined metadata/head/autogenerate comparison, actual late upgrade/downgrade rollback, cooperating advisory locks/real DDL timeout, explicit destructive targets and retained facts versus lost delivery history. Actual Redis composition preserves prior contracts; old service /ready intentionally reports 503 at the new head. Re-upgrade has empty inbox history and can apply the same key again. Finite reported evidence does not award mastery (ADR 0030).


## Bounded delivery recovery practice

Four lessons and the Delivery recovery lab add explicit poison redrive, saved-budget/generation guards, current-group payload pruning and retained-inbox replay. Relevant libraries remain SQLAlchemy, Psycopg 2, redis-py, pytest, mypy and Python dataclasses/importlib.resources; no new academy runtime dependency is needed. The Lua adapter is supplied. 36 installed finite cases and four manual criteria provide evidence, not an expert certification (ADR 0031).


## Local release operating boundary

Four ordered lessons (python-release-settings through python-release-evidence), eight original scenarios under Release operating contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery release lab. Its authenticated fourteen-file starter has three unfinished functions, 33 public cases (15 offline/18 live) and four manual criteria. Eight installed packages on owned PostgreSQL/Redis verify private copied settings, compatible delivery_004 readiness, preserved business contracts, real failures, one owned disposal, installed operating commands/loopback SIGTERM cleanup and exact rollback losses with re-upgrade. Reported evidence does not award mastery (ADR 0032).


## Local SQL query analysis boundary

Five ordered lessons (python-query-joins through python-query-evidence), ten original scenarios under SQL query analysis contracts and complete guided/diagram/glossary/private recall layers connect to the SQL query analysis lab. Its authenticated nineteen-file starter has three unfinished SQL queries, 36 public cases (23 offline/13 PostgreSQL) and four manual criteria. Nine installed packages verify complete-key/fanout/empty reports, zero-safe revision windows, newest-before-JSONB filtering, read-only owned queries, source compatibility and actual result-equivalent baseline/indexed plans on 40,000 records/notes. Five literal lesson SQL examples also run on PostgreSQL. Reported evidence does not award mastery (ADR 0033).


## Local API depth boundary

Five ordered lessons (python-http-validators through python-api-depth-evidence), ten original scenarios under separate API delivery contracts and complete guided/diagram/glossary/private recall layers connect to the API depth lab. Its authenticated fourteen-file starter has three unfinished functions, 51 public cases (39 offline/12 PostgreSQL) and four manual criteria. Nine freshly installed packages verify private conditional GET/permission ordering, framed raw-byte HMAC/freshness/strict events, atomic scoped receipts/readings, real competing duplicates/conflicts/rollback/lock timeout and compatible prior routes. The saved actual loopback HTTP report observes 200/304/change, 401/403/409/422/503/retry, committed counts and released connections. Reported tests and manual review do not award mastery (ADR 0034).


## Composed practical-review tools and limits

Five lessons (`python-practical-contracts` through `python-practical-review`), ten original scenarios and complete guided/diagram/glossary/private recall layers connect to the Composed Python practical review lab. Its authenticated eighteen-file starter has three unfinished functions, 50 public cases (47 offline/three PostgreSQL) and four manual criteria covering all seven advanced review dimensions. Eight freshly installed local packages compose strict old service pages, latest/conflict/domain adapters, immutable typed snapshots, response/resource ownership, bounded cache and actual thread/spawn workers. A stated 128-fact workload gives equivalent reporting outputs with 152/32 computations and 120 hits; a cyclic case gives 64/64 and zero hits. Actual cProfile call counts, raw wall/CPU intervals and Python allocation observations have no speed threshold. The original-case/regression/design task feeds fixed manual submissions and revisions. Maintainer fixtures and reported tests never establish learner originality, mastery or expertise (ADR 0035).

Use standard-library cProfile/pstats, time.perf_counter_ns/process_time_ns and tracemalloc for separate CPU/work/allocation observations; preserve old dataclass/generic/context/cache/process contracts. HTTPX/Uvicorn and FastAPI/Pydantic/SQLAlchemy/Psycopg 2/Alembic supply actual local service boundaries. Pytest, mypy, build and Ruff are development tools. These are role-specific working targets, not a universal list of every Python library. Profiled fingerprints are a stated synthetic workload; broader production/security/expert judgment remains open.


## Offline model contracts

Six lessons (`model-request-contracts` through `model-contract-evidence`), twelve original scenarios under separate **Model call contracts** and complete guided/diagram/glossary/private recall layers connect to the Model contracts lab. Its authenticated fourteen-file starter has three unfinished functions, **84 offline public cases** and four manual criteria. A clean installed standard-library package normalizes two invented provider formats; checks pinned model/prompt/schema, copied complete-envelope context/output admission, strict complete/refused/incomplete proposal/usage variants; and reserves fictional credits before attempts, settles only valid usage, retains unknown reserves and stops at cost/step/one cooperative deadline boundaries. Actual waiting fixtures verify timeout cleanup and propagated external cancellation. Installed JSON records eleven finite cases without raw prompts/refusal reasons/exceptions. No real model, network, current pricing, provider conformance or semantic quality is claimed (ADR 0036).

For this applied AI role, standard-library asyncio, typing.Protocol, dataclasses and json support the local model boundary. Pytest/mypy/build/Ruff are development tools; provider SDKs/tokenizers would be integration-specific choices, not universal Python proficiency gates. No new Python knowledge exam or expert certification is added.


## Scoped retrieval contracts

Six lessons (`retrieval-chunk-identities` through `retrieval-evidence`), twelve original scenarios under separate **Scoped retrieval contracts** and complete guided/diagram/glossary/private recall layers connect to the Scoped retrieval lab. Its authenticated fifteen-file starter has three unfinished functions, **83 public cases** and four manual criteria. The installed standard-library package preserves complete chunk keys/character offsets/digests, validates model/version/dimensions/finite nonzero vectors, chooses latest revisions before trusted tenant/group/activity/metadata filters, then computes exact cosine or simple ASCII token-set Jaccard ranking with full-key ties. Requested-k precision, labelled recall and first-relevant rank use explicit denominators; no-label cases have null recall/rank and separate unwanted-hit counts. Four computed reports use an original 12-revision/15-chunk/nine-query development fixture with hand-supplied six-dimensional vectors. No real embedding model, ANN/database index, held-out quality, durable document lifecycle or automatic mastery is claimed (ADR 0037).

The local retrieval lab uses dataclasses, hashlib, math, re, json, importlib.resources and importlib.metadata from the standard library. Pytest/mypy/Ruff/build/setuptools/wheel are development tools. Embedding SDKs and PostgreSQL/pgvector are integration-specific production choices, not universal Python proficiency gates. No new Python exam or expert certification is added.


## RAG continuation (2026-10-11)

The connected applied-AI path now includes model contracts, scoped retrieval and RAG practice. RAG composes asyncio, dataclasses/typing, JSON/hashlib and sqlite3 with the two published local packages. Standard-library mechanics and controlled provider checks do not constitute an expert Python evaluation. Existing beginner/intermediate/advanced Python banks and the 152 dedicated Python lessons remain unchanged; semantic AI evaluation and tool security are still planned.


## Tool-use continuation (2026-10-11)

The applied-AI path now includes connected authorized tool practice after model/retrieval/RAG. asyncio, dataclasses/typing, JSON/hashlib, pathlib and sqlite3 plus the published local packages are the necessary mechanics; pytest/mypy/Ruff/build/setuptools/wheel support development. Controlled proposals and local receipts do not establish expert Python or real model competence. Existing 152 dedicated Python lessons, 304 Python scenarios and original level banks remain unchanged. AI evaluation/security/final path audit is the remaining fixed step-six milestone.


## Final step-six evaluation (2026-10-12)

The connected applied-AI release lab adds asyncio, dataclasses/typing, JSON/hashlib, importlib.resources/metadata, fractions, pathlib/tempfile and the four published local packages; pytest/mypy/Ruff/build/setuptools/wheel support verification. Its 54 finite public cases and controlled metrics are separate from Python expertise. The existing 152 Python lessons, 304 Python scenarios and 72 level-evaluation questions remain unchanged. Fixed step six is complete; comprehensive portfolio/practical exams and operational reliability remain steps seven/eight.
