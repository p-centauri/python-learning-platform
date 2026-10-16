# ADR 0007 — Python foundations and a local project contract

Date: 2026-09-20
Status: accepted

## Context
The user approved the first complete Python foundations module, with simple lessons, exercises and an expense-tracker CLI. The academy already supported Markdown lessons, objective grading and project checklists, but only had one dedicated Python lesson and no isolated learner-code runner.

## Decision
Publish nine ordered lessons and 18 distinct objective exercises as `python-foundations-module` within the existing Python track. Preserve all existing IDs and attempts. Use the separate `Python foundations` skill so new beginner exercises do not change the existing Python ownership skill denominator. Publish catalog revision `2026.09-foundation-v2`; exam snapshots remain unchanged.

Each lesson follows explanation, example, guided practice, independent work and explained checking. This is a complete bounded path to the expense CLI contract, not completion of all Python topics. Expose module grouping and derive UI exercise counts from authored metadata.

Provide an authenticated starter ZIP from an explicit six-file allowlist. Include a complete CLI wrapper, three intentionally unfinished learner functions, sample input/output, a precise README and 13 public acceptance tests. Keep the maintainer reference outside the download. Do not accept paths or learner source through this endpoint. Learners run Python locally; the API only serves files.

Use integer cents, one currency with two decimal places, exact input validation and all-or-error JSON output. Project milestones remain self-reported. Passing local tests provides useful evidence but is not a recorded code grade or certification. The final lesson gives an explained implementation approach; a reviewer still inspects code and additional learner tests.

## Verification
Run the public suite against the reference and confirm the unfinished starter fails as intended. Execute trusted lesson examples in test subprocesses. Check content/prerequisite integrity, answer secrecy, authenticated download contents, learner isolation and unchanged mastery for reading/checklists. Verify the lesson-to-practice-to-project browser journey and existing journeys, then build the frontend.
