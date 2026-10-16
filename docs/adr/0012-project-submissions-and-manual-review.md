# ADR 0012 — Project submissions and manual review

Date: 2026-09-30
Status: accepted

## Decision
Implement learning-experience step 2 for all seven existing projects: persistent drafts, fixed submitted artifacts, project-specific pinned rubrics, self-review, invited-account human review, and new revisions linked to their preceding submission. Preserve old project checklists as self-report. No grading, reading or mastery model changes.

Author four criteria per project and a shared evidence-based 0–3 scale in `content/project-rubrics.json`, version `2026.09-project-review-v1`. Freeze the complete rubric when creating a draft. Later rubric changes apply to new drafts, never old submissions or their feedback.

Store normalized submission/assignment/feedback activity in three new tables. A submission owns a JSON artifact (HTTPS repository URL, fixed revision reference, design explanation, implementation evidence, reported local test command/output/status and change summary) and a JSON rubric snapshot. These are authored/user document snapshots, not replacements for relational ownership, revision or review identity.

## Lifecycle and access
- One current draft per learner/project through serialized mutations; creating again resumes it. Save partial drafts, explicitly discard drafts, or submit after validating required evidence. Submitted versions are immutable and repeated submission is idempotent.
- Starting a revision copies the preceding artifact, pins the current rubric, and clears its change summary. Submitting requires an explanation of changes. Feedback and reviewer assignments remain tied to their original version. There is a 50-version local limit per learner/project and 10 distinct reviewer accounts per submitted version.
- The owner explicitly invites a registered account by normalized email. Invitations grant access only to that submitted artifact, rubric and feedback. No outbound email, notification integration, repository fetch, code execution or automated test result ingestion occurs.
- Reviewer qualifications and real-world identity are not verified. Existing authentication has no email verification; an invitation targets an already registered account and the UI identifies its judgment as manual. Public deployment still needs stronger identity and abuse controls.
- Reviewer access can be revoked or restored. Revocation prevents future reads/reviews without deleting recorded feedback. The review inbox lists only active invitations for the signed-in account; drafts and unrelated learner state are never shared.
- Review identity and self/human classification come from the authenticated user. Every pinned criterion requires a strict integer rating and evidence; summaries and next actions are required. Feedback is immutable, one review per account/version, with identical retries returning the saved review. All ratings at least 2 produce “Meets stated rubric”; otherwise “Changes requested”. Neither outcome awards mastery or certifies expertise.
- PostgreSQL user-row locks serialize owner mutations; submission-row locks serialize invitation changes and review recording. SQLite migration and local behavior are verified separately from future PostgreSQL concurrency tests.

## Limits and next step
The academy preserves submitted text and references, not a repository mirror. A reviewer must inspect the named commit; a URL or tag can change externally. Test output is learner-reported and rendered as plain text. This release supplies the complete manual submission/review/revision workflow, not verified implementation grading or comprehensive project certification.

After reporting verified step 2 completion, wait for the user's next “continue”. Step 3 is a separate isolated coding/SQL runner with execution quotas and resource/network isolation.
