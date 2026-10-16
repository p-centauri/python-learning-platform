A release evaluation needs a stable question: which exact behavior are we measuring? If cases, labels or thresholds change between runs, a higher score may simply mean an easier test. Keep case IDs, expected boundaries, dataset purpose and policy versions explicit. The local lab packages eighteen original development cases with the code. They cover four retrieval cases, seven evidence-answering cases and seven tool cases.

The dataset loader rejects missing or duplicated scenarios, unknown fields and unsupported versions. Labels use complete scoped source keys. The ordinary and malicious-source answer cases cannot lose their human-review requirement. Every candidate observation must match one case exactly, and one run cannot mix candidate versions. A partial run is an incomplete evaluation, never an empty perfect result.

A canonical dataset digest identifies the complete case definition. The default release policy pins that digest. Changing a relevance label changes the digest, so the old policy cannot approve the edited dataset silently. Candidate observations also have a digest, including source identities, actual outcomes and configured model/prompt/schema. A prior review cannot be copied to a changed candidate merely because its display name stayed the same.

The fixture purpose is development-controlled. It uses hand-assigned vectors and reproducible providers, so it helps inspect boundaries while building. It is not held-out evidence of a learned model's generalization. Choose future representative and adversarial data separately, record how it was collected and protect it from tuning. The academy stores reported commands and manual evidence; it does not authenticate a learner's local report. Versioning makes a claim reviewable, rather than automatically making it trustworthy.

## Guided practice

Predict the printed result, then explain which evaluation boundary this small illustration leaves untested.

```python
expected_version = "ai-release-fixture-v1"
loaded_version = "edited-v2"
print(loaded_version == expected_version)
```

## Independent practice

Load the fixed resource, reject incomplete or duplicate coverage, and demonstrate that a changed label cannot reuse the pinned gate or a prior candidate review.

## Check your work

Record dataset purpose, exact versions/digests and complete case IDs. Separate development inspection from held-out model quality.

Use the [AI release evaluation project](/projects#ai-evaluation). Record commands, versions and failures. Reported tests and manual review remain separate from mastery.
