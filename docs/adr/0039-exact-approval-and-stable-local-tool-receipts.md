# ADR 0039: Exact application approval and stable local tool receipts

Date: 2026-10-11

Status: Accepted

## Context

Model/retrieval/RAG labs provide bounded proposals and current citation evidence, but no authorized side-effect loop. Fixed milestone eight requires simple tool teaching, strict proposal/permission boundaries, budgets and replay evidence without executing learner code or granting the model authority.

## Decision

Publish `academy-tools-lab==0.1.0`, depending on the completed RAG package and composing four local packages outside the academy runtime. Add six connected lessons/twelve scenarios under a separate skill, a fifteen-file authenticated starter with three unfinished functions and four manual project criteria. Catalog/layer versions become `2026.10-tools-v1`/v25; previous exams, skill denominators and fixed histories are preserved.

Permit only source_excerpt(selected citation) and save_note(selected citation,bounded label). Own a distinct strict `tool-proposals-v1` call/finish/refused/incomplete schema with pinned model and bounded exact usage. Proposal fields cannot carry tenant/actor/role/URL/approval. Application Context supplies authority scope, selected exact citations and stable operation_id. Current Authority callback and RAG resolution are checked around provider/tool waits and immediately before effects/replay. A canonical digest binds policy/scope/operation/tool/label/exact citation to a trusted application approval. The digest identifies parameters; it is not a signature or grant.

Use a separate explicitly initialized `tool-store-v1` SQLite store. One immediate transaction checks a scoped application operation receipt, compares its action fingerprint, applies caps and commits note/receipt together. Identical actions replay the original note even with new model call IDs or after reopen; different actions conflict even after reapproval. A late receipt error rolls back the note. Current access/approval still applies before replay. Connections close and never span awaits.

Use public model configuration/Request/Provider/Adapter with full canonical request-byte/output admission, pre-attempt fictional reservation, strict validated settlement, finite steps and one shared cooperative deadline. Stop on blocked/invalid/uncertain outcomes without automatic effect retry. Actual trusted fixture waits model timeout before an effect and after a committed effect. External cancellation propagates with awaited cleanup; explicit stable-operation reconciliation observes the saved receipt. Public reports redact source text and pin provider/model/prompt/schema; only currently permitted prompt history receives read excerpts.

## Evidence

All 81 public tool cases pass on maintained source and installed wheels, alongside prior 84 model, 83 retrieval and 70 RAG cases in one clean four-package installation. Strict package/demo, pip/quiet typed imports, seventeen actual experiment reports and saved JSON readback pass. Tests observe changed permission/source/approval, regenerated IDs, conflicting payload, caps/reopen/late rollback, one deadline across waits, uncertain post-commit timeout and external cancellation. Sixty-nine focused backend checks, four browser journeys, lint, learner-data preservation and unchanged migration head are recorded in the dated PROGRESS entry.

## Consequences and limits

Atomic replay covers only this local note and receipt transaction. It does not guarantee remote email/payment/API effects exactly once or eliminate the source-index/note-store revocation race. A committed historical note is not undone by a rejected later result and grants no current source access. Trusted callbacks/metadata and final observation points are assumptions, not complete production authentication or distributed authorization. Byte units/fictional cost/cooperative waits are not token invoices, hard interruption or durable cancelled-call accounting. Fixed providers and hand vectors do not assess real model planning or hostile injection resistance. No network tool, shell/path execution, production store or automated mastery is added. AI evaluation/security/final audit remains, so step six stays open.
