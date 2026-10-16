# ADR 0006 — Advanced Python knowledge evaluation

Date: 2026-09-20
Status: accepted; extends ADR 0005

## Decision
Add an advanced Python bank with 28 questions, four per topic: object model/protocols, typing/API contracts, resource lifetime/isolation, async failure/cancellation, concurrency/process boundaries, performance/memory, and packaging/verification. It assumes intermediate fluency and targets Python 3.13+; implementation-specific concurrency questions state their GIL/build assumptions explicitly.

Reuse immutable attempt snapshots, independent bank resume, server grading and the existing provisional 80% overall/60% per-topic policy. For this bank that requires at least 23/28 overall and 3/4 in each topic. Keep results separate from mastery. Display levels in beginner/intermediate/advanced order after the mixed diagnostic.

Provide library expectations, official reading references and a concrete practical project with reviewer evidence criteria. The knowledge test is available immediately; practical submission and recorded review remain future work. Passing multiple-choice questions does not certify advanced implementation ability. No learner-code execution, schema changes or new dependencies are introduced.

## Verification scope
Extend the shared API and browser journeys to the advanced bank. Check secrecy, ownership, independent resume, snapshot stability, grading thresholds and study feedback. Run authored prediction examples only in test subprocesses. Keep the original banks and their saved attempts unchanged.
