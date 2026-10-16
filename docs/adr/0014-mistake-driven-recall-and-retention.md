# ADR 0014 — mistake-driven recall and separate retention evidence

Date: 2026-09-30
Status: accepted for the bounded local release

## Context

The original review queue repeats a multiple-choice scenario. Recognizing its answer, especially after viewing a solution, does not establish that a learner can retrieve an idea later. The agreed learning-experience step 4 requires recurring mistake signals, different questions and retention evidence that stays separate from recognition and mastery.

## Decision

Author `content/review-questions.json`, version `2026.09-recall-v1`, policy `2026.09-retention-v1`. All 38 published lesson topics map their 76 original scenarios to two new short-answer variations each: 76 questions total. Prompts ask for specific values or terms and have simple explanations. Exact grading accepts only authored strings, trims surrounding whitespace and follows each question's declared case rule. It does not infer semantic understanding, grade essays, call an LLM or execute submitted text. Trusted prediction snippets run only in maintainer content tests.

The authenticated recall router derives topic signals from the account's original scenario attempts and recorded recall sessions. Two or more wrong answers flag repeated errors; distinct original-question counts are displayed so repeating one mistake is not presented as broad coverage. This is a review signal, not a diagnosis of a misconception. Exams, coding checks, reading and project judgments are not mapped into these signals.

Starting a check pins its full question, accepted strings, explanation, source IDs, content/policy versions, prior interval and whether the ID was unseen. Active responses allowlist only the prompt, optional code, format, case rule and the learner's saved answer/help declaration. The key, explanation and validation snippet stay server-only until submission. Submitted answers/results are fixed; repeat submission returns the existing result. Discarded drafts record viewing without a grade.

Every started question counts as seen, including discarded drafts. Prefer unseen IDs, then the least recently viewed current variant. A content version bump alone never makes a viewed ID fresh. Exhausting the two-question bank produces explicitly labelled repeats, without new-question credit. Historical results use their pinned snapshots even after content edits. Future substantive question changes need new IDs; a future grading-policy change needs a new policy and explicit compatibility handling.

## Evidence and scheduling

Display separate correct/total counts for original scenario recognition, immediate short-answer practice, fresh delayed checks, repeated delayed practice and assisted work. A scheduled unseen check with no reported help counts as fresh delayed evidence whether its answer is correct or incorrect. Independence is self-reported. A new original scenario attempt during an active check also marks it assisted. Reading notes or using outside help cannot be reliably detected; the interface explains this limit.

Initially, an incorrect original answer schedules one day later and a correct one three days later. A topic started only through recall schedules a day after its first exposure. Subsequent delayed submissions set the next interval: correct independent fresh answers grow it to at least three days, then double up to 30; correct repeated questions retain the interval; wrong or assisted delayed answers reset it to one day. Later mistakes bring an extended schedule forward. Every recorded scenario attempt or viewed/submitted recall question requires at least another 24 hours before a new delayed check. Resuming an existing active check is allowed. These are provisional practice rules, not a validated memory model.

Immediate practice is always available and starts a new gap; it never becomes delayed evidence merely because a draft is left open. Topic history distinguishes immediate, assisted, fresh and repeated work. Neither workflow changes mastery, legacy review rows, exams, reading or project progress.

Plan policy `2026.09-plan-v2` prioritizes due checks and active drafts within the goal's route and estimated budget. It avoids duplicate original-scenario tasks for those topics during that queue calculation. Other due legacy reviews remain supported. Dashboard notices and scenario feedback link to the new workflow.

## Storage and access

Migration `f064de537b42` adds `recall_sessions`, retaining prior tables. Unique learner/active-topic keys permit one resumable question per topic. Every query includes the authenticated account ID; mutation authorization uses the existing learner-row lock. Strict answer/help inputs, 120-character answers, 20 new starts per ten minutes and 2,000 starts per account bound this release. Existing drafts remain resumable at the limit. PostgreSQL locking/concurrency is still unverified; SQLite is the verified local store.

## Verification and limits

API/content/migration tests cover ownership, private fields, drafts, fixed snapshots/results, help, due gates, mistakes, finite-bank reuse, exact case, plan prioritization and unchanged mastery. Browser checks use dedicated accounts. One local fixture ages only a newly created `recall-e2e-…@example.com` account's original practice attempts to simulate a due check; there is no public time-changing endpoint. That fixture does not claim real elapsed-time longitudinal learning.

This bank covers the published lesson topics, not the unfinished expert curriculum. Two variants per topic provide limited fresh evidence. Free-form rubric grading, personalized memory calibration, normalizing a concept graph and incorporating exam/coding evidence remain separate work. Legacy scenario mastery retains ADR 0004's existing rules.
