# Build contract

## Evidence domain

Model tenants, memberships, documents, immutable source versions, jobs, chunks with offsets, ACLs, vector-space identity, evaluation datasets/candidates and citations. Replaced/deleted or permission-revoked versions must not appear as current support. Store raw content only with a declared access/retention policy. Vector dimensions alone do not identify a model space.

## Ingestion contract

Accept declared text/PDF formats with size/type limits and bounded parser work. A stable tenant/source/version digest identifies ingestion. Preserve original location, language, offsets and ACLs through retries/chunking. Replace/deletion revokes current support; reprocessing is idempotent. Queue bounded jobs, record failure categories and reconcile uncertain completion. A parser is not a sandbox for hostile files.

## Query and citation API

POST /ask accepts {query,language,k}; derives actor scope, performs authorized retrieval before any model call, returns {status,answer,citations:[{source_id,version,chunk_id,offset}]}. No support returns status=no-support and no invented answer. GET /citations/{id} rechecks current ACL/version before exposure. Citation IDs, caches and rerankers must not bypass scope.

## Retrieval experiments

Build lexical and vector baselines, then hybrid candidates and a reranker. Pin dataset split, model space, chunking, index settings and candidate revision. Report requested-k precision, positive-label recall/MRR, no-answer/unwanted hits, denominators, latency distribution and actual cost with units. Review answer support/semantic quality separately; exact citation matching is not correctness.

## Dataset and holdout

The pack supplies 30 synthetic labeled multilingual seed questions with source IDs and development/held-out split. Expand and independently verify labels for your corpus. Do not tune on the held-out questions or present synthetic labels as real-company/population evidence. Include boundary/colliding IDs, no-answer, stale/private sources, exact names, lexical vs semantic misses and permission changes.

## Security and failure matrix

Required: foreign tenant text; revoked ACL in cache/citation; same chunk ID under different tenants; stale source; incompatible embedding versions; empty retrieval; duplicate ingestion; parser failure; provider timeout/refusal; malicious source instructions; reranker leaking candidates; model/tool role escalation. Treat source text as evidence, never approval. Demonstrate observed boundaries and residual semantic risk.

## Operations and scale

Ship migrations/Compose with PostgreSQL+pgvector, bounded ingestion workers, read/write pool budgets, current schema/readiness, backpressure and safe traces. State measured corpus/workload/quality, storage/index growth and budget. Exercise replace/delete, provider outage and restore. Explain ACL/vector rebuild after restore; do not claim millions-of-documents performance from a small fixture.

## Final review packet

Use existing evaluation, ingestion, retrieval and security criteria. Provide fixed repository, source/version examples, permission matrix, reproducible candidate reports, labels/splits, redacted failure traces, citation access tests, human answer judgments and deployment/recovery evidence. Downloaded fixtures/checklists do not award mastery.

## Libraries and abilities

- FastAPI/Pydantic: ingestion, query, citations and strict output contracts
- PostgreSQL, SQLAlchemy, Alembic and pgvector: source/version/ACL storage and compatible vector spaces
- Parser/chunker chosen for declared formats: offsets and bounded ingestion
- Embedding provider adapter: pinned model/version/dimensions and time/cost budgets
- Hybrid search and reranking adapters: deterministic baselines and measured candidates
- pytest/HTTPX and an evaluation harness: held-out labels, denominators and failure cases

## Official references

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy session ownership](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [pgvector contracts and indexing](https://github.com/pgvector/pgvector)
