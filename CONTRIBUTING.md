# Contributing

Read AGENTS.md and the durable status files before starting. Keep changes reviewable, distinguish working features from planned ones, and append verification evidence at session closeout.

## Add a track or module
Add a stable ID, title, description and ordered topics to `content/catalog.json`. Add a module with its `track_id`. Planned tracks may appear in the path, but must not link to empty lesson pages. Seed the relational catalog after changing definitions.

## Add a lesson
Create `content/lessons/<stable-id>.md` and its metadata. Declare prerequisites, objectives, source readings, skill and exercise references. Write for an experienced developer: show a failure, explain the mental model, include code or SQL, discuss tradeoffs and give a practical mastery check. Do not claim a module is complete because it has one lesson.

Use simple explanations at every level, including advanced Python. State the result, explain why in ordinary words, walk through a small example, then show the common mistake and the fix. Define jargon before relying on it. Preserve important version/runtime limits. Follow the coverage and authoring guidance in `docs/PYTHON_LEARNING_PATH.md`; a topic appearing in an assessment is not a complete lesson.

## Add an exercise
The current supported format is single-answer objective scenarios. Supply a unique scenario, 3–4 credible options, a zero-based answer index, three progressive hints, and an explanation of both the correct approach and common wrong reasoning. Keep answer keys in API-only content. Do not label a multiple-choice exercise as an automated implementation assessment.

Additional answer formats require a domain grading policy, request/response schemas, UI, authorization tests and a rubric or isolated execution service as appropriate.

## Add an exam question
The original pilot lives in `content/catalog.json`; additional banks live in `content/assessments/*.json`. Use stable bank/question IDs, explicit content versions, credible distractors and explained answers. Do not reuse practice questions. State scope, topic coverage, learning targets, limitations and any separately reviewed practical follow-up. Bump the content version when published questions or policies change. Existing attempts retain server-only definition snapshots; never rewrite those snapshots to match new content.

Test answer secrecy before submission, category recommendations, grading boundaries, bank-specific resume and snapshot stability after content changes. Trusted authored code-prediction fixtures may declare `validation_output` for subprocess validation in the test suite. This is not a learner-code runner; never add learner code execution to the API. Keep library guidance in the content files and `docs/PYTHON_LEVELS.md`, distinguishing standard-library modules, third-party packages, tools and optional specializations.

## Add a project
Add a title, domain brief, stack and stable milestone IDs. Each milestone should specify concrete evidence such as tests, diagrams, metrics or runbooks. Milestone checkboxes are self-reported progress, not grading.

## Review checklist
- Does a visible control actually work?
- Is the change scoped to the authenticated learner?
- Could a client forge a score or obtain an active exam answer?
- Can repeated requests corrupt state or inflate mastery?
- Are failure messages clear and retry paths usable?
- Are keyboard focus, labels, mobile layout and safe rendering preserved?
- Have relevant tests and STATUS/PROGRESS/ROADMAP been updated?


## Local release operating boundary

Four ordered lessons (python-release-settings through python-release-evidence), eight original scenarios under Release operating contracts and complete guided/diagram/glossary/private recall layers connect to the Delivery release lab. Its authenticated fourteen-file starter has three unfinished functions, 33 public cases (15 offline/18 live) and four manual criteria. Eight installed packages on owned PostgreSQL/Redis verify private copied settings, compatible delivery_004 readiness, preserved business contracts, real failures, one owned disposal, installed operating commands/loopback SIGTERM cleanup and exact rollback losses with re-upgrade. Reported evidence does not award mastery (ADR 0032).

Run `make verify-delivery-release` for this trusted reference chain only. Keep the exact starter allowlist, no reference keys, simple runnable lesson examples, independent tasks, complete interaction/recall layers and frozen old evidence. Do not use the verifier for learner uploads. The fixed next milestone is SQL query depth/plans.


## Local SQL query analysis boundary

Five ordered lessons (python-query-joins through python-query-evidence), ten original scenarios under SQL query analysis contracts and complete guided/diagram/glossary/private recall layers connect to the SQL query analysis lab. Its authenticated nineteen-file starter has three unfinished SQL queries, 36 public cases (23 offline/13 PostgreSQL) and four manual criteria. Nine installed packages verify complete-key/fanout/empty reports, zero-safe revision windows, newest-before-JSONB filtering, read-only owned queries, source compatibility and actual result-equivalent baseline/indexed plans on 40,000 records/notes. Five literal lesson SQL examples also run on PostgreSQL. Reported evidence does not award mastery (ADR 0033).

Run `make verify-query-analysis` for the maintained SQL reference chain only. Preserve exact starter/private-key boundaries, three labelled unfinished SQL queries, complete teaching layers and old submitted history. The verifier separately evaluates the five literal PostgreSQL lesson examples. Record actual workload/results/plans and cleanup; never evaluate uploads with it or force scans/timing to manufacture a pass.


## Local API depth boundary

Five ordered lessons (python-http-validators through python-api-depth-evidence), ten original scenarios under separate API delivery contracts and complete guided/diagram/glossary/private recall layers connect to the API depth lab. Its authenticated fourteen-file starter has three unfinished functions, 51 public cases (39 offline/12 PostgreSQL) and four manual criteria. Nine freshly installed packages verify private conditional GET/permission ordering, framed raw-byte HMAC/freshness/strict events, atomic scoped receipts/readings, real competing duplicates/conflicts/rollback/lock timeout and compatible prior routes. The saved actual loopback HTTP report observes 200/304/change, 401/403/409/422/503/retry, committed counts and released connections. Reported tests and manual review do not award mastery (ADR 0034).


## Composed advanced Python practical review

Five lessons (`python-practical-contracts` through `python-practical-review`), ten original scenarios and complete guided/diagram/glossary/private recall layers connect to the Composed Python practical review lab. Its authenticated eighteen-file starter has three unfinished functions, 50 public cases (47 offline/three PostgreSQL) and four manual criteria covering all seven advanced review dimensions. Eight freshly installed local packages compose strict old service pages, latest/conflict/domain adapters, immutable typed snapshots, response/resource ownership, bounded cache and actual thread/spawn workers. A stated 128-fact workload gives equivalent reporting outputs with 152/32 computations and 120 hits; a cyclic case gives 64/64 and zero hits. Actual cProfile call counts, raw wall/CPU intervals and Python allocation observations have no speed threshold. The original-case/regression/design task feeds fixed manual submissions and revisions. Maintainer fixtures and reported tests never establish learner originality, mastery or expertise (ADR 0035).

Preserve the exact eighteen-file authenticated ZIP and three unfinished functions; maintain solutions only under reference/. Keep the reviewer task independent of assessor fixtures. Verify installed result equivalence, actual profile call counts, cleanup and compatibility; never enforce timing or memory improvements. Preserve private guided/recall keys, old exam/skill denominators and submitted snapshots. Record reported versus objective versus manual evidence accurately.


## Offline model contracts

Six lessons (`model-request-contracts` through `model-contract-evidence`), twelve original scenarios under separate **Model call contracts** and complete guided/diagram/glossary/private recall layers connect to the Model contracts lab. Its authenticated fourteen-file starter has three unfinished functions, **84 offline public cases** and four manual criteria. A clean installed standard-library package normalizes two invented provider formats; checks pinned model/prompt/schema, copied complete-envelope context/output admission, strict complete/refused/incomplete proposal/usage variants; and reserves fictional credits before attempts, settles only valid usage, retains unknown reserves and stops at cost/step/one cooperative deadline boundaries. Actual waiting fixtures verify timeout cleanup and propagated external cancellation. Installed JSON records eleven finite cases without raw prompts/refusal reasons/exceptions. No real model, network, current pricing, provider conformance or semantic quality is claimed (ADR 0036).

Preserve the exact fourteen-file ZIP, three unfinished functions and references outside the starter. Test both invented wire formats without implying a named-provider emulation. Validate fixture context/reservation edges, distinct outcomes, unknown usage and cooperative lifetime behavior; never present predetermined replies as semantic evaluation. Preserve old exams/skills/account records and pinned artifacts. Trusted maintainer verification never runs learner uploads.


## Scoped retrieval contracts

Six lessons (`retrieval-chunk-identities` through `retrieval-evidence`), twelve original scenarios under separate **Scoped retrieval contracts** and complete guided/diagram/glossary/private recall layers connect to the Scoped retrieval lab. Its authenticated fifteen-file starter has three unfinished functions, **83 public cases** and four manual criteria. The installed standard-library package preserves complete chunk keys/character offsets/digests, validates model/version/dimensions/finite nonzero vectors, chooses latest revisions before trusted tenant/group/activity/metadata filters, then computes exact cosine or simple ASCII token-set Jaccard ranking with full-key ties. Requested-k precision, labelled recall and first-relevant rank use explicit denominators; no-label cases have null recall/rank and separate unwanted-hit counts. Four computed reports use an original 12-revision/15-chunk/nine-query development fixture with hand-supplied six-dimensional vectors. No real embedding model, ANN/database index, held-out quality, durable document lifecycle or automatic mastery is claimed (ADR 0037).

Preserve the exact fifteen-file starter, three unfinished functions and reference outside its allowlist. Keep original fixed fixture labels and manually supplied vectors explicit; compare both methods under the same scope and denominator conventions. Test permission/revision ordering, empty/no-label metrics and actual installed resources/reports. Never present this data as a learned-model benchmark or run learner uploads in the API.


## RAG continuation (2026-10-11)

Keep RAG teaching and private assessment keys in content files. Preserve the exact starter allowlist, three learner TODOs, previous skill denominators and fixed submitted versions. For changes to RAG behavior run `make verify-rag`, the focused `test_rag` API tests and affected Playwright journey, then `make lint`. Test failures must not be converted into skips or weaker contracts. Record finite objective observations separately from reported/manual evidence and real semantic quality; current catalog/layer revisions are `2026.10-rag-v1`/v24. Update the status/roadmap/progress handoff and ADR for consequential contract changes.


## Tool-use continuation (2026-10-11)

Keep tool teaching/private keys outside React. Preserve the exact fifteen-file allowlist/three learner TODOs, earlier denominators and frozen submitted versions. Use `make verify-tools`, focused `test_tools` API checks, affected Playwright journeys and `make lint` for tool changes. Never weaken failures into skips or conflate returned results with actual committed effects. Current catalog/layers are `2026.10-tools-v1`/v25. Record consequential authority/replay changes in an ADR and update durable handoff documents.


## Final step-six evaluation (2026-10-12)

Keep the versioned evaluation resource, strict schema/pinned dataset policy, complete observations and manual judgments separate. Run `make verify-ai-evaluation`, `make audit-learning-paths`, affected API/browser checks and `make lint`; preserve earlier definitions and submitted artifacts. Catalogue/layers are `2026.10-ai-evaluation-v1`/v26. Never promote incomplete data, synthetic mutations or self-reported judgments into real model/security/mastery claims. The fixed step-six sequence is complete; step seven begins only on the user’s next continuation.

## Comprehensive evidence changes

Knowledge supports strict single-choice, exact-set multiple-response and manually reviewed short text. Design commits stages before exposing later incidents. Practical definitions pin an execution digest; bump the version whenever the published contract/starter changes. Do not rewrite old attempts/runs/review attachments. Author private fixtures only in server content; exact pack allowlists exclude references. Use the private isolated controller, never API interpreters. Keep new rubric IDs/counts explicit, original criteria unchanged and written judgments separate from objective scores/mastery. Add real lifecycle/secrecy/ownership/replay and browser coverage; see ADR 0041.
