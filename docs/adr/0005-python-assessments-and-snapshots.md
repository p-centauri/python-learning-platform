# ADR 0005 — Separate Python evaluations and frozen attempt definitions

Date: 2026-09-20
Status: accepted

## Context
The user requested beginner and intermediate Python tests, their library expectations, and the status of advanced evaluation. The existing mixed diagnostic used a single live question bank. Supporting multiple evolving banks requires stable grading and independent saved attempts.

## Decision
Author new banks in API-only `content/assessments/*.json`, retaining the original pilot and compatibility defaults. Start/resume scopes to both learner and bank. Every new attempt stores a deep copy of its complete definition, content version and policy in JSON. All subsequent question display, answer validation and grading use that snapshot. Public active responses allowlist safe question fields.

Backfill historical pilot attempts from a frozen definition embedded in migration `b92a4d781f10`; do not read mutable catalog files during migration. Preserve existing answers/results. Unknown legacy definitions fail closed instead of silently grading against current questions. This change pins exams only, not historical learner enrollments or the full curriculum.

Beginner has 20 questions across five topics; intermediate has 24 across six. The provisional target is 80% overall and 60% per topic, checked without display rounding. Results are limited knowledge evidence: retakes reuse questions, practical follow-ups require separate review, and exam scores do not change mastery. A dedicated advanced Python evaluation remains planned.

Library expectations distinguish built-in modules, third-party packages, tools and optional backend/AI specialization. The learner does not need every framework to qualify at a Python level.

## Consequences and verification
Snapshots duplicate small authored definitions but keep attempts reproducible across edits/removals. They contain answer keys and must never be serialized directly. API/content tests cover privacy, independent resume, ownership, grading boundaries, snapshot stability, trusted prediction fixtures and legacy migration preservation. Browser tests cover both new banks through saved answers, resume, submission, feedback and mobile layout. Learner code is never executed by the API.
