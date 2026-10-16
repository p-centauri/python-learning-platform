# Database model

## Implemented in M1
- `learning_preferences`: learner ID as primary/FK, goal, weekly hours (1–20), starting approach and updated timestamp. Check constraints enforce supported values.
- `lesson_checkpoint_attempts`: owner/lesson/checkpoint, unique learner/UUID request key, selected index, full private definition snapshot, fixed guided feedback and timestamp. Reading/mastery state stays separate.
- `coding_drafts`: unique learner/exercise, saved source and updated timestamp.
- `coding_attempts`: learner, UUID request key unique per learner, exercise, fixed source/private definition snapshot/result JSON and timestamp.
- `recall_sessions`: owner/topic/question, active/submitted/abandoned lifecycle, immediate/delayed mode, full private definition snapshot, saved short answer/help declaration, fixed result and timestamps. Unique learner/active-topic keys enforce one resumable check per topic; closed rows clear the active key.
- `users`: normalized unique email, display name, password hash, created timestamp.
- `sessions`: hash of opaque token, user FK, expiration.
- `curriculum_versions`: version identifier and title.
- `tracks`: stable identifier, display order, description, version FK.
- `modules`: track FK, title, sequence.
- `lessons`: module FK, title, skill identifier, Markdown path, duration, metadata.
- `lesson_progress`: unique learner/lesson, completed timestamp.
- `exercise_attempts`: learner/lesson/exercise ID, selected answer, score, hint count, revealed status, time.
- `exercise_states`: unique learner/exercise, hints unlocked, solution revealed.
- `review_items`: unique learner/exercise, due date, interval and repetitions.
- `notes`: unique learner/lesson, body, updated timestamp.
- `bookmarks`: unique learner/lesson.
- `exam_attempts`: owner, assessment identifier, lifecycle, server-only definition snapshot JSON (including version and grading policy), answers JSON, result JSON, timestamps.
- `project_progress`: unique learner/project/task, completion timestamp.
- `project_submissions`: owner/project/revision uniqueness, parent version FK, draft/submitted status, artifact and rubric snapshot JSON, creation/update/submission timestamps.
- `project_review_assignments`: unique submission/account-email invitation, active access flag and timestamp. Grants apply only to submitted versions and can be revoked without removing feedback.
- `project_feedback`: submission and authenticated reviewer FKs, unique reviewer/version, server-derived self/human kind, criterion ratings/evidence JSON, summary, next actions and timestamp.

Stable content identifiers refer to immutable definitions in a versioned content bundle. Lessons/modules/tracks are projected into relational tables for integrity. Answer keys remain server-only content. JSON is appropriate for frozen assessment snapshots, not a replacement for normalized learning activity.

## Subsequent migrations
Migration `b92a4d781f10` adds assessment snapshots and backfills existing pilot attempts with their frozen historical definition. The nullable column supports detection of unknown legacy content; attempts without a known snapshot cannot resume or submit. Upgrade/downgrade and preservation of existing answers/results are tested with SQLite.

Migration `c731ab204e19` adds optional per-learner planning preferences. No existing user, attempt, note or progress row is changed. The plan itself is computed from current content and activity, not stored as a second progress record.

Migration `d842bc315f20` adds the three project workflow tables without backfilling or altering prior learning state. Downgrade removes only those new tables, in dependency order. SQLite upgrade/downgrade preservation and schema drift checks are covered by tests.

Migration `e953cd426a31` adds coding drafts and fixed attempts. Existing accounts, learning preferences and project artifacts survive tested upgrade/downgrade/re-upgrade. Complete definitions remain server-only; public feedback is redacted.

Migration `f064de537b42` adds recall sessions only. Schedules and mistake counts derive from existing scenario attempts and this new history, avoiding a second mutable progress record. Tests cover upgrade/downgrade/re-upgrade while retaining accounts, preferences, project artifacts and coding source/results. The local pre-migration backup is `.local/recall-20260930/academy-before-migration.db`.

Migration `a175ef648c53` adds lesson checkpoint attempts only. Upgrade/downgrade/re-upgrade checks retain accounts, coding source/results and recall history. The local backup is `.local/interactive-20260930/academy-before-migration.db`; direct comparison checks prior rows in 15 learning tables.

Future work: normalize concepts/skills and prerequisite edges; standalone exercises/hints/solutions; project/task definitions; full exams/sections/questions/answers; version-pinned learner enrollments. Keep this target explicit rather than creating dozens of unused tables.

## Integrity and access
Unique constraints prevent duplicate progress. Each learner query includes the authenticated user ID. Foreign keys prevent orphaned records. Index user-scoped attempts and review due dates. All timestamps use UTC. PostgreSQL account recovery/session-lock tests are verified in ADR 0042; broader domain concurrency remains open. SQLite cannot validate row-lock behavior.

## Everyday access migration

Migration c3970b860e75 follows b286fa759d64 and adds account_recovery_keys only: owner primary/FK, SHA-256 token digest, created timestamp and optional consumed timestamp. Existing accounts/learner rows are not backfilled or rewritten. Clone SQLite and PostgreSQL upgrade/check/downgrade/re-upgrade preserve all prior learner/business rows; downgrade discards only the new recovery keys. Re-upgrade cannot recover those discarded keys. Actual backup/restore fingerprints cover all 25 current tables. PostgreSQL restricted role/setup and safe recovery into new targets are described in [OPERATIONS](docs/OPERATIONS.md).
