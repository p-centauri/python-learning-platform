A baseline is a simple method used for comparison. It helps you see whether extra complexity changes the result you care about. The lab compares exact cosine ranking with keyword set overlap on the same documents, queries, labels and access rules. Holding these inputs fixed makes differences easier to explain. A changed dataset or different permission scope would make the comparison less useful.

The keyword method lowercases text and extracts ASCII letters and digits into a set of tokens. Its score is intersection size divided by union size, called Jaccard similarity. Repeated words do not increase this score because a set keeps each token once. This intentionally simple tokenizer does not handle every language or word form. It is not BM25 or a production search engine. A query with different wording may have low overlap even if a person considers the passage useful.

Exact cosine scanning calculates a score for each eligible vector. The bounded lab has at most 64 corpus chunks and does not need an approximate index. Large deployments may use ANN to trade search cost against missed candidates. PostgreSQL and pgvector indexing, approximate recall, hybrid ranking and reranking remain planned work; this in-memory scan does not implement them. The hand-assigned vectors also make semantic wins a fixture property rather than a learned-model result.

Sort by descending score and then ascending complete chunk key. A deterministic tie rule prevents input order from changing equal-score results. Apply an optional inclusive minimum score after scoring; its meaning depends on the method. A lexical threshold and a cosine threshold are not interchangeable confidence levels. Compare k=1 and k=3, inspect per-query hits, and record both positive and missing-evidence outcomes. Do not tune a threshold on this tiny fixture and call it a universal safety guarantee.

## Guided practice

Predict the printed result, then explain which retrieval boundary this small illustration leaves untested.

```python
a = {"retry", "request"}
b = {"retry", "safe"}
print(len(a & b))
```

## Independent practice

Compare cosine and lexical modes at k=1/3. Reverse input order to verify ties remain stable. Explain a query with differing results and a mode-specific threshold tradeoff.

## Check your work

Label exact scans, ASCII set Jaccard and hand-supplied vectors correctly; no ANN, BM25, hybrid or real-model benchmark is implemented.

Use the [Scoped retrieval project](/projects#retrieval). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
