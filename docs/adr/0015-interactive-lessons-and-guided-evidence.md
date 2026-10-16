# ADR 0015 — interactive lessons and guided evidence

Date: 2026-09-30
Status: accepted for the bounded local release

## Context

Step 5 adds active work to published lessons: prediction checkpoints, small debugging tasks, diagrams, a glossary and accessible navigation. Reading and guided recognition must stay separate from mastery and independent delayed recall.

## Decision

Author `content/lesson-interactions.json`, version `2026.09-interactive-v1`, policy `2026.09-guided-v1`. Each of the 38 published lessons has a prediction and a “find the smallest useful fix” task, with three choices and a simple explanation: 76 checkpoints, 38 diagrams and 76 glossary definitions. Educational content stays outside React. Native figures and ordered lists show diagram relationships with equivalent text; no external renderer is required. The glossary filters terms/definitions, links back to teaching and participates in global search.

These are guided choice checks, not arbitrary code editing, essay assessment or delayed retention evidence. The isolated coding lab provides executable practice. API grading compares a strict selected index with a private key and never executes submitted text. Trusted author prediction snippets execute only in maintainer tests.

Each successful submission stores fixed account-owned feedback: answer, full private definition snapshot, version/policy, expected choice, explanation and timestamp. Public unsubmitted questions omit keys, explanations and validation snippets. The latest 50 attempts per lesson are returned with their original wording/options, preserving history across content changes. Latest feedback for the current version survives reload. Unsaved choices are transient; the UI promises saved feedback, not saved unsubmitted answers. Repeating a revealed task remains labelled guided practice.

Inputs require an index, current version and UUID key. Replaying the same successful request returns its stored result, including after content changes. A conflicting key or a stale new submission is rejected. Existing learner-row mutation locks and a unique learner/key constraint protect writes; PostgreSQL concurrency remains unverified. Limits are 40 recorded attempts per ten minutes / 4,000 per account; replay remains available at the limit.

## Navigation and state boundaries

Markdown second-level headings receive positional IDs mirrored by a server section list that skips fenced code. Native section links focus their targets. Asynchronously loaded diagrams/glossary also support direct fragments. Previous/next links stay in the published track; prerequisites use real titles. End-of-track navigation returns to the learning path. Reordering sections can change an old fragment's meaning; historical lesson/enrollment pinning remains future work.

Checkpoint results never change mastery, reading completion, exams, projects, coding history or legacy review rows. A submission is recorded study exposure: it starts another 24-hour gap before a new delayed recall check for that topic, and a submission during an active recall check counts as observed assistance. Wrong checkpoint answers are not inferred as recall misconceptions or counted as original recognition. Prior fixed recall results remain unchanged. Viewing diagrams/glossary is not tracked; outside help and unrecorded reading retain ADR 0014's self-report limits.

Migration `a175ef648c53` adds `lesson_checkpoint_attempts` only. Back up the local database before upgrade and compare existing rows afterwards. Content, API/migration, keyboard, fragments, failed-save retry and desktop/mobile checks verify this feature. No runtime dependencies, exam versions or scenario mastery denominators change.

## Limits

This completes the interaction layer for published lessons, not the unfinished expert curriculum. Two guided choices per lesson offer finite practice. No arbitrary essay grading, execution inside lessons, mastery gating or full accessibility certification is claimed. Curriculum expansion remains step 6; broad reliability/accessibility hardening remains step 8.
