# ADR 0041 — Portfolio contracts and frozen comprehensive evidence

Date: 2026-10-12. Status: accepted.

## Problem

Three portfolio cards had milestones and manual reviews but no complete build experience. The original brief also requires distinct knowledge, executable repair and incident-driven senior design assessments. A choice score cannot establish practical delivery or senior judgment.

## Decision

Keep the three existing portfolio IDs, milestone IDs, criteria and history. Add author-controlled build briefs and exact authenticated seven-file packs: README, complete brief, deliberately unfinished application factory, public HTTP acceptance tests, synthetic fixtures, pytest configuration and an unfilled evidence template. These are learner assignments, not completed production implementations. Required release, PostgreSQL, worker, provider and multilingual evidence belongs to the learner and reviewer. Thirty RAG seed labels and 24 finance workflow seeds are synthetic and visible; the holdout split is a discipline, not independently secret/unseen population evidence. Human language/intent review is pending.

Add three separate comprehensive definitions. The 150-minute knowledge bank has 48 original questions, eight areas, 24 single-choice, sixteen multiple-response and eight written explanations. Exact-set scoring covers forty objective questions; eight manual responses are excluded from that percentage. Targets remain provisional, not calibrated readiness or certification. Weak categories link to real lessons/scenarios. The 300-minute practical exam has a deliberately broken standard-library order/AI application, eight public regressions and fifteen additional private cases. The 240-minute design exam commits four baseline responses before revealing seven incidents sequentially. Earlier responses remain fixed. All durations are advisory elapsed time since start, including breaks; there is no forced expiration, pause accounting or proctoring.

Extend ExamAttempt with a bounded JSON workspace for flags, saved position, practical source and committed stage facts. ExamRun records exact source, fixed definition and validated/redacted actual runner results with an account-scoped UUID retry key. Existing attempt definitions, answers/results, learner state and original banks stay unchanged. Additive migration b286fa759d64 follows a175ef648c53; verify a private clone upgrade/downgrade/re-upgrade and model drift separately from live deployment.

The API stores source and calls the existing authenticated loopback Docker controller. It never imports or interprets learner code and accepts no filesystem uploads/paths. The controller selects one fixed authored execution contract; identity, version and canonical execution digest must match the frozen attempt. A later incompatible publication fails closed rather than silently grading an old attempt against new cases. Fresh non-root, no-network, read-only, memory/CPU/PID/time/output limited containers receive case inputs without expected outputs. Private outputs/names/messages are redacted again at the API boundary. Limit runs to eight per ten minutes and 64 per attempt. A matching source run is required to submit; failed checks may be submitted honestly. Unavailable/invalid runner output records no grade, while the separately saved draft survives.

Submission atomically fixes exam state and creates one submitted review attachment using the frozen rubric. Complete written responses, source and actual finite check result are attached server-side; clients cannot submit an attachment or a grade. Existing registered-account invitations, revocation, attributable self/human feedback and immutable revisions provide review. A later revision omits the generated attachment and retains the original as its parent. A standalone review draft is practice, not another exam result. Current feedback is visible in the review workspace; no manual percentage, reviewer qualification, mastery or readiness is invented.

## Limits

The repair harness tests the offline core. Actual SQLite rollback and query-count traces, sequential duplicate/permission/cache behavior and cooperative async cleanup do not prove PostgreSQL concurrency, distributed broker durability, HTTP/Docker deployment, load performance or learned-model semantics. Approval hashes/principals are fixture authority, not real approval issuance or authenticated identity. Exact source quotes can contain unsafe instructions; semantic quality and end-to-end authority still require review. Architecture, actual infrastructure failures, deployment and operational claims use the seven manual criteria and repository evidence.

The academy's full deployment/recovery/export/accessibility acceptance remains step eight. No new runtime dependency, public email message, model provider, mastery formula or original content denominator is introduced. Portfolio products must still be built by the learner; full expert curriculum remains broader than these finite assessments.

## Verification

See the dated PROGRESS entry, STEP_7_PORTFOLIO_EXAMS checklist and `.local/portfolio-exams-20261012/` for actual isolated results, API/browser/build/migration/preservation evidence. Remote CI is configured but unobserved.
