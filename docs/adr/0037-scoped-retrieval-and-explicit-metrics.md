# ADR 0037: Scoped retrieval and explicit finite metrics

Date: 2026-10-11
Status: accepted

## Context

The sixth fixed step-six milestone requires labelled retrieval data, chunk/vector identities, access/metadata filters, similarity limits and measured baseline ranking. The existing similarity introduction is not enough for installed implementation practice. We need deterministic evidence without treating a downloaded model, a tuned tiny dataset or a similarity score as truth, permission or expertise.

## Decision

Publish six simple connected lessons under separate Scoped retrieval contracts, with complete private guided/recall, accessible diagrams and glossary. Serve an exact fifteen-file authenticated starter with three unfinished functions (make_chunks/retrieve/evaluate), 83 public cases and four manual criteria. The maintained operations stay outside the ZIP; a standalone standard-library package is not an academy runtime dependency. Previous scenarios/exams and frozen learner artifacts remain unchanged.

Use original fixed development judgments for 12 document revisions, 15 chunks and nine queries (seven positive-label/two no-label), with manually supplied six-dimensional fixture-v1 vectors. The fixture deliberately includes tenant/group exclusion, old/current/inactive documents, metadata-empty results and a keyword trap with quoted irrelevant log-label terms. No model generates vectors. Compare actual exact cosine and lowercase ASCII token-set Jaccard rankings on the same input at k=1/3; neither ANN, BM25 nor hybrid search is implemented.

Chunk keys contain tenant/document/revision/ordinal. Preserve exact character offsets/text and SHA256 of UTF-8 bytes; overlap and final-tail behavior are fixed, with whole-call failure above 32 windows. A digest checks identity, not authority. Validate exact copied immutable values, coherent model/version/dimension metadata, finite bounded nonzero vectors and a corpus of at most 64 unique complete keys.

Find latest revision per full tenant/document before active/access/topic/document filters. Old public text cannot return after a private or inactive update. Application-owned Principal is distinct from query text; public or any-of-group candidates must pass scope before either scoring method and before top k. Coherent complete current corpus/revision metadata is a supplied assumption. Atomic reindexing, deletion/tombstones, authentication and a full production permission service are not supplied. Reports contain key/offset/digest/score, not raw document text/vectors/ACL fields.

Cosine uses hypot/fsum and rounding clamp to [-1,1]; scale does not change direction and negative values are meaningful. Optional inclusive thresholds are mode-specific, not confidence guarantees. Ties sort by complete key. Validate judgment keys under the same latest/access/metadata scope before threshold, rejecting missing/inaccessible/obsolete labels.

Precision uses requested k, recall uses relevant-label count, reciprocal rank uses the first relevant position or zero. Macro precision includes every case; recall/MRR include only positive-label cases. No-label cases have null recall/rank and a separate unwanted-return count. Empty observations have null averages and make no corpus-quality claim. The packaged fixture is UTF-8/byte-bounded/duplicate-free/exact-field JSON; supported metadata and resource identity are checked.

The installed demo computes four reports with versions and per-case keys/scores. Saved JSON readback must match the serialization of actual results. Learners add a predicted independent regression and tradeoff note for labelled manual review; the API never executes uploads or awards mastery from reported tests.

## Verification and consequences

Maintained source and fresh outside-source archive/wheel installation pass all 83 cases without skips, six strict-typed package/demo files and pip/quiet import/location/py.typed/fixture checks. Tests observe pre-score exclusion, latest-before-access/no fallback, scope, compatibility, stable ties, Unicode slices, cap failure, exact denominator edges and no-label results. Installed reports measure the keyword trap and actual mode/k differences without inferring general quality.

Focused content/API, interactive/recall/project-version and browser journeys verify connected teaching, private keys, exact authenticated ZIP, saved manual evidence and finite mobile layout. Existing learner/session/evidence rows are preserved through reseed; academy migration and private runner are unchanged. Required checks and corrected test-selector/count issues are recorded in PROGRESS.

The sixth fixed milestone is complete as finite teaching/practice. Three remain: RAG, tool use, AI evaluation/security/final audit. Real embeddings, ANN/pgvector operations, corpus lifecycle, held-out quality and public authorization require independent evidence. Step 6 and later academy operations stay open; RAG is the exact next action.
