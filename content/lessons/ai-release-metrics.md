A useful metric says what counted and what did not. Retrieval precision in this lab divides relevant returned hits by requested k, even when fewer rows return. Its macro average includes all four retrieval cases. Recall divides found relevant hits by the label count and averages only the two positive-label cases. Mean reciprocal rank uses the first relevant position over those same positive-label cases.

The other two cases have no relevance labels. Do not invent recall one when they return nothing. Count their unwanted returned hits separately. Raw cosine retrieves an unwanted passage for a quasar question because the hand vector points toward the file document. The task-term gate removes that hit using application-supplied terms. A separate threshold case still misses a labelled passage, keeping positive recall at one half. Report this miss even when the illustrative gate accepts the candidate.

Fraction arithmetic preserves exact ratios and inclusive boundaries. Precision is one quarter, positive recall and reciprocal rank are one half on this fixture. These are measured local values, not recommended production targets. A stricter threshold should fail rather than being rounded into a pass.

Seven RAG cases measure expected answer presence, outcome and exact current citation support. Seven tool cases measure expected stop and local effect counts. A timeout after a committed note expects one effect, not zero. Permission failures, privacy leaks and unexpected boundary outcomes are counted separately. An aggregate quality number must not hide an unauthorized action. Exact quotation support does not measure truth, relevance or useful explanation; those require separate semantic review. The complete report includes denominators so another person can reproduce the interpretation.

## Guided practice

Predict the printed result, then explain which evaluation boundary this small illustration leaves untested.

```python
from fractions import Fraction
relevant_hits = 1
requested_k = 3
print(Fraction(relevant_hits, requested_k))
```

## Independent practice

Implement explicit precision/positive recall/MRR and unwanted-hit conventions. Test requested k, empty results, exact thresholds and unexpected permission/effect facts.

## Check your work

Name every denominator. Distinguish exact answer/tool contracts, semantic usefulness and current permission; never turn no labels into a perfect score.

Use the [AI release evaluation project](/projects#ai-evaluation). Record commands, versions and failures. Reported tests and manual review remain separate from mastery.
