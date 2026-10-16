# ADR 0038: Document lifecycle and current RAG evidence

Date: 2026-10-11

Status: Accepted

## Context

The published model-contract and scoped-retrieval packages verify finite proposals/rankings. They do not manage durable source updates/deletions or keep generated citations aligned with current access. Fixed step-six milestone seven requires a bounded installed evidence-answering lab, simple connected teaching and honest manual assessment.

## Decision

Publish `academy-rag-lab==0.1.0`, depending on the two existing 0.1.0 lab packages, outside the academy runtime. Keep educational layers outside React, three learner functions unfinished and maintained implementations outside the authenticated fifteen-file starter. Add six connected lessons/twelve scenarios under a separate skill and four manually reviewed project criteria. Current catalog/layer versions become `2026.10-rag-v1`/v24; previous exams, skill denominators and frozen artifacts are preserved.

Use an explicitly separate local SQLite index with `rag-store-v1` and a monotonic epoch. Publish complete source/vector/metadata/ACL state atomically; exact replay is a no-op, older/conflicting publication fails and tombstones survive reopen. Cap identities including tombstones and chunks. Own/close each connection and never hold a transaction across a provider await. This is local lifecycle evidence, not the PostgreSQL production design.

Compose trusted tenant/group/activity/metadata filtering and exact cosine retrieval with a limited required-term gate, keyword reranking and deterministic whole-passage UTF-8 packing. Bind local selected IDs to complete source keys, text, offsets and digests. Reuse public Request/Adapter/Provider/configured model limits; own the distinct `rag-quotes-v1` JSON schema rather than reusing the earlier triage decoder. Permit one controlled call after full serialized input/output/cost admission. Strictly validate bytes, JSON fields/variants, model/schema/usage and one or two distinct exact selected whole quotes.

Refresh application-owned Principal before use and after a valid proposal. Rebuild/compare the bundle, epoch and current citation resolution before exposing text. Any source epoch change conservatively invalidates the plan. Missing evidence, malformed/refused/incomplete output or changed authority/source returns no answer text. Cancellation propagates with awaited cooperative cleanup. The computed report records actual calls and local accounting, never invented accuracy.

## Evidence

Three built source archives/wheels are installed outside source. All 70 RAG public cases pass in installed and maintained-source runs; the prior 84 model and 83 retrieval cases pass against the composed installation. Strict package/demo, quiet imports, pip and JSON report readback pass. Seventeen computed experiments and tests observe update/delete/reopen, replay/conflict/rollback, whole-context admission, private/foreign exclusions, fabricated quotes/citations, missing evidence, changed permissions/source, timeouts and external cancellation. Focused content/API, browser workflows, lint, unchanged migration head and learner-record preservation are recorded in the 2026-10-11 PROGRESS entry.

## Consequences and limits

Exact quotes establish provenance against the selected current source, not truth, semantic relevance, entailment or free-form answer quality. Hand vectors, lexical task terms and controlled providers are development fixtures; no held-out learned-model benchmark is claimed. Chunk boundaries can split useful meaning. Trusted metadata/application authority and the final observation point are explicit assumptions; later reuse needs current resolution. Epoch invalidation is conservative, not a distributed concurrency protocol. There is no answer cache, URL fetch or tool execution. Local SQLite/fictional cost/cooperative timeouts are not production PostgreSQL, real token invoices, hard isolation or a durable call ledger. Manual review does not award mastery. Tool use and AI evaluation/security/final audit remain open, so step six is not complete.
