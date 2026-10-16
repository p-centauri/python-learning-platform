Retrieval finds candidates; it does not decide that each candidate answers the question. The lab first uses the published cosine retriever with trusted tenant, group, activity and metadata filters. Only authorized candidates can move forward. A high similarity score never permits a private document to enter model context. Query or document text cannot replace the application principal.

The application supplies one to three required task terms. A candidate must contain all these lowercase ASCII words in its token set. This small gate makes missing-evidence cases reproducible. It is intentionally limited: matching words can still be irrelevant, conflicting or misleading, and useful evidence can use different wording. It is not a general semantic relevance check. Keep the gate definition separate from user and document instructions, and evaluate its false passes and misses before broader use.

Rerank surviving candidates by simple keyword set Jaccard against the question, then by cosine and complete source key. The method is a transparent baseline rather than a learned reranker. Record the vector and keyword roles instead of calling any extra sorting “AI.” Candidate count and selected passage count are bounded independently. A passage omitted during this stage may explain a later answer failure even when retrieval found it.

Pack whole selected chunks into a UTF-8 byte budget that includes their evidence IDs, source keys, offsets, digest and text. An accented character or emoji uses more than one byte. Skip a passage that does not fit; do not cut its text or remove a meaningful exception silently. The complete provider request has its own context check because instructions and the question also occupy space. The Bundle pins the source epoch, scope, gate and policy so the answer stage can detect a changed plan before a call.

## Guided practice

Predict the printed result, then explain which evidence boundary this small illustration leaves untested.

```python
text = "é🙂"
print(len(text.encode("utf-8")))
```

## Independent practice

Implement prepare. Retrieve allowed candidates, apply the stated task-term gate, rerank with deterministic ties, and pack whole evidence under exact UTF-8 boundary tests.

## Check your work

Explain a retrieval miss versus a gate/ranking/budget omission. Word overlap and byte fixture units cannot establish general relevance or real token counts.

Use the [Evidence answering project](/projects#rag). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
