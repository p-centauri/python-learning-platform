# Original reviewer artifact

This task is unfinished until you design and explain your own case. The public fixtures and maintainer's assessor example are not evidence of your originality. Automated checks validate finite data claims; a reviewer assesses originality, usefulness and design judgment.

Create one UTF-8 JSON file <=8192 bytes with exactly these fields:

| Field | Contract |
| --- | --- |
| case_id | Nonempty text, <=32 characters, identifies your independent case. |
| namespace | The earlier bounded lowercase ASCII namespace shape. This is data scope, not authorization. |
| purpose | Nonempty <=1000-character explanation of which incorrect implementation the case should catch. |
| rows | <=256 objects with exactly id/revision/value, old service bounds; report conversion also keeps <=60000 values. |
| requests | <=256 exact integer positions into the sorted latest selected Items. Empty is allowed. |
| expected_latest | <=64 ordered id/revision/value objects, predicted before running; conflicts should be tested separately as a regression. |
| expected_computations | Exactly baseline and cached exact integers 0..256; predict reuse/eviction with capacity eight. |

Run `demo.py --case your-case.json --output practical.json`. The data-only helper never executes or imports the file. It checks expected latest values/counts and ordered baseline/candidate equivalence. Its result says originality requires manual review. Do not describe the helper as an originality detector or an expert grader.

Add a separate original regression in your repository. State the proposed incorrect change, expected refusal or result, why the published fixtures do not fully cover your concern, and actual output. Include at least one of: namespace/revision boundaries, obsolete-key conflict, narrower-domain refusal, streaming cancellation/partial setup, cache reuse-distance counterexample, or supported caller warning/identity preservation. Choose a justified case rather than copy a sample and rename it.

Write a decision note connecting all seven advanced dimensions:

1. Object/type and input/output contracts; immutable copies and static versus runtime evidence.
2. Resource handoff, partial setup failure and borrowed owner rules.
3. Async cancellation/response cleanup and uncertain blocking effects.
4. Page/body/row/request/cache/worker/pending bounds and limits of count bounds.
5. Worker-local resources, serialization, actual spawn and joined shutdown.
6. Stated workload/scope/cache state, equivalent outputs, actual profiles/raw intervals/Python allocation interpretation.
7. Built archives/wheels, outside-source install/versions, old service/deprecated caller regressions and failure evidence.

Use the in-app project: save a draft with exact repository and revision, artifact paths/evidence/commands, then submit a fixed revision. Reviewers use four grouped criteria with labelled self/human feedback. Revised submissions preserve prior artifacts and feedback. A reviewer should identify demonstrated behavior, missing evidence and a concrete next revision; a successful test bank alone cannot establish expertise. Keep credentials, DSNs and private raw error logs out of the artifact.
