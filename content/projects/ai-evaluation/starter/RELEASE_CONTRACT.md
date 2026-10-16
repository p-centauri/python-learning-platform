# Controlled release contract v1

## Frozen inputs and observations

The package loads release-cases.json explicitly on demand, never at import. Strict 1..32768-byte UTF-8 JSON rejects duplicate fields/nonfinite constants/unknown fields, wrong version/purpose/scenario/layer, malformed relevance keys, inexact bool/integers and missing/duplicate fixed scenarios. Suite requires all 18 fixed scenario identities and cannot remove the two semantic-review flags. The dataset purpose is development-controlled; no held-out claim is accepted. A canonical suite digest pins default ai-gate-v1. Editing labels changes that digest and cannot reuse the old policy silently.

observe uses a caller-owned existing empty directory, refuses an existing workspace, creates one case directory per validated ID and awaits the supplied actual composed harness sequentially. Candidate version is raw-cosine-v1 or task-gated-v1. Source index/local note databases remain separate. The harness uses actual prior retrieval, RAG and tool operations with controlled providers, current trusted authority and limited application task terms. It records source keys/digests, actual call charges/counts, note counts/replay, outcome/support/permission/leak/cleanup facts and actual embedding model/version/dimensions and model/prompt/schema. No raw source/query/tool arguments/exception appear in Observation. Internal synthetic markers test exposure; they are not real credentials.

## Exact measurements

measure requires one exact Observation per Case and one candidate version, with complete identity alignment and selected count no greater than requested k. Macro precision averages relevant hits/requested k over all four retrieval cases. Recall averages relevant hits/label count over the two positive-label cases; MRR averages reciprocal first-relevant position over the same two. Two unlabelled cases have no recall/MRR claim; count returned unwanted hits separately. Fraction arithmetic preserves exact boundaries. Empty results are not perfect scores.

Seven RAG cases measure expected reason/answer presence and exact current citation support. Seven tool cases measure expected stop/effect counts, including the uncertain timeout that already committed one local note. Permission and privacy failures and finite expected-boundary failures are counted separately across all 18 cases. These are contract metrics, not factual answer accuracy, entailment or planning quality. Metadata/authority/harness observations are trusted fixture inputs; manually forged reported observations are not independently certified.

## Objective gate and reported quality review

ai-gate-v1 pins the suite digest and exact inclusive thresholds: precision at least 1/4, positive recall/MRR at least 1/2, answer/tool contract rates 1, no unlabelled unwanted hits and zero permission/privacy/boundary failures. These are illustrative development thresholds derived for this fixture, not recommended production release targets. The raw variant fails an unwanted hit; the task gate removes it while retaining a threshold miss and recall 1/2. Lower recall is still visible.

Dataset or candidate changes invalidate a prior review. Reviews must address a flagged case exactly once and pin both digests; reviewer/source/verdict/note are explicit bounded data. Self/human identity and qualifications are not authenticated by this local package. Objective pass does not fill in a missing review; manual rejection blocks even if objective checks pass. No review can override an objective failure. controlled_fixture_ready means only the specified finite fixture checks and reported review are complete. The guarded demo leaves quality reviews pending and never creates an approval.

## Security, privacy and limits

The adversarial matrix observes role/URL/tool-field rejection before local effects, changed source rejection, missing-evidence no calls, actual cooperative timeout cleanup and persisted note count after tool timeout. A socket-connect denial test observes zero network attempts in the controlled matrix. This is not an SSRF-safe general fetcher or a real model's prompt-injection immunity. There is no network tool. A malicious source may be faithfully quoted without expanding permissions; exact support alone cannot deem that answer semantically safe.

Reports expose only finite keys/digests/counts/versions/reasons and rational metrics. Neither raw excerpts nor private synthetic markers are printed. One explicitly labelled simulated regression mutates a permission observation to demonstrate the gate; do not report it as an actual unauthorized provider action. Temporary owned databases are removed by the guarded demo. No learner code runs in the academy API. Real model/token costs, permanent/distributed authority, hard isolation, remote exactly-once and learner originality remain unverified. Reading, reported tests and manual reviews never award mastery.
