# ADR 0011 — Personal learning plans

Date: 2026-09-30
Status: accepted

## Decision
Implement the first user-approved learning-experience step as a saved personal plan, without beginning project submissions or the runner. Persist only the learner's goal, weekly whole-hour budget (1–20), starting approach and update time in a one-row-per-user `learning_preferences` table. Migration `c731ab204e19` adds this table without backfilling or changing existing progress. Existing accounts see an optional setup prompt; registration remains usable without choosing a plan.

Keep authored goal routes and topic-to-lesson guidance outside React in `content/learning-plans.json`, version `2026.09-plan-v1`. A deterministic service builds recommendations from published lessons, the learner's reading/practice, due reviews and the latest submitted result of each assessment. Never inspect an active assessment for placement or return private snapshot fields. Learner-owned queries and existing mutation protection apply.

## Recommendation policy
- Support Python, backend, applied AI and the combined goal. Routes include prerequisite closure and list only published material. Recommendations are guidance, not enforced mastery gates.
- Schedule due reviews first, then unresolved incorrect practice, relevant weak assessment topics, unfinished practice for read lessons and the remaining path. Deduplicate an exercise scheduled for review and practice.
- A category below 80% using exact correct/total counts can suggest a related lesson. This threshold is guidance, not calibration. The mapping explicitly reinforces foundations and does not claim complete coverage of advanced topics. Where teaching is absent, say so and link to submitted study guidance.
- Weak assessment remediation needs correct practice after that submission to leave the queue; a correct answer predating the failed assessment does not resolve it. Correct practice may include assistance and does not itself certify independent competence.
- A submitted Python bank meeting its existing knowledge target can suggest an entry point. Earlier lessons remain accessible and incomplete. Show unread immediate prerequisites, and let the learner choose the beginning instead. Reading completion alone always leaves unfinished practice available.
- Fill an ordered rolling queue up to the chosen weekly budget. Use authored reading estimates and 10-minute practice/review estimates; stop before an item that does not fit rather than rearranging learning to fill minutes. Unused time is shown. This is not a dated calendar, time tracker or graduation estimate.
- Recompute on visiting/refreshing the plan and after saving preferences. The dashboard displays the same first action. No plan endpoint writes lessons, attempts, reviews or mastery.

## Boundaries and follow-up
This step adds planning only. It does not alter grading, enforce prerequisites, execute code, provide a review workflow, predict employability or complete the curriculum. All next learning-experience steps require the user's next “continue”. Step 2 is project submissions, rubric feedback and revision history.
