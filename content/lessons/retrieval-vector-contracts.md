An embedding is a list of numbers used to represent input for a particular model. Similarity compares vectors within a compatible space. Two lists with the same length are not necessarily compatible: different models or revisions can assign different meanings to their coordinates. Record the configured model identity, version and dimensions with both stored chunks and the query. A dimension match alone cannot justify comparison.

The lab supplies six-dimensional vectors by hand. No function converts text into a learned embedding, and no provider account is needed. These vectors let you test exact ranking and permissions without relying on a changing external service. They cannot measure a real model's semantic understanding. A future integration must pin and verify its supported model and regenerate or migrate stored vectors under an explicit lifecycle policy.

Check current runtime values before calculating. A vector is an immutable tuple with the configured length. Coordinates are finite integers or floats, excluding booleans. The fixture bounds their magnitude and rejects zero or extremely small norms. NaN can break ordering; infinity can break arithmetic; a zero vector has no direction for cosine comparison. Type annotations help a checker, but do not validate incoming bytes or corrupted values.

Cosine similarity compares directions using a normalized dot product. Positive values indicate alignment in this space, zero indicates orthogonality, and negative values indicate opposition. Scaling a valid vector does not change its direction. Use math.hypot for norms and math.fsum for the sum, then clamp rounding to the interval from -1 to 1. The score is not a probability that a passage answers the question. Even a score of 1 cannot establish truth, authority or real-world relevance. Keep those conclusions separate in your report.

## Guided practice

Predict the printed result, then explain which retrieval boundary this small illustration leaves untested.

```python
from math import hypot
print(int(hypot(3, 4)))
```

## Independent practice

Validate model/version/dimensions and finite nonzero vectors. Add a wrong-model regression with matching dimensions, and test scale, negative scores and zero rejection.

## Check your work

State why the hand-supplied vectors and a cosine score cannot establish real embedding-model quality.

Use the [Scoped retrieval project](/projects#retrieval). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
