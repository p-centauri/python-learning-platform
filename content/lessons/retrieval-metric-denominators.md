A retrieval metric needs an explicit question and denominator. Precision@k asks how many of the requested result slots contain relevant evidence. In this lab it is matching hits divided by requested k. If you request three hits and only one relevant hit returns, precision is one third even if that is the only returned result. This convention counts missing slots as zero. Other evaluations may use different conventions; record yours before comparing numbers.

Recall asks what fraction of the labelled relevant chunks returned. If there are two relevant labels and one matching hit, recall is one half. Reciprocal rank focuses on the first relevant result: a first relevant hit at rank two contributes one half; no relevant hit contributes zero. Average reciprocal rank over positive-label cases is MRR. These measures describe different behavior, so one cannot replace the others.

Some queries have no relevant evidence in the fixture. Their recall and reciprocal rank are undefined here, represented by null rather than a perfect score. They still contribute zero precision and get a separate unwanted-hit count. Average recall and reciprocal rank only over cases with positive labels. Report the count of those cases as well as the no-label count. An empty evaluation returns null averages; no observations cannot establish perfect retrieval.

Labels must name existing eligible latest chunks under the query's tenant, groups and metadata filters. Reject missing, obsolete or inaccessible labels instead of treating them as hard misses. Validate judgments before the score threshold so a threshold-induced miss remains visible as lower recall. These are complete judgments for this small original development fixture, not general labels for the internet or a held-out test of an embedding model. Reusing this data to tune and report results provides development evidence, not an unbiased estimate of future quality.

## Guided practice

Predict the printed result, then explain which retrieval boundary this small illustration leaves untested.

```python
matched = 1
requested = 3
print(f"{matched / requested:.2f}")
```

## Independent practice

Implement evaluate using actual retrieve output. Verify requested-k precision, labelled recall, first-relevant rank, threshold misses, invalid labels and separate no-label macro denominators.

## Check your work

Include case counts and unwanted returns with the averages. An empty evaluation or no-label case must never invent perfect recall.

Use the [Scoped retrieval project](/projects#retrieval). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
