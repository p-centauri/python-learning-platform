## An embedding compresses context
An embedding maps text into a numeric representation learned for a particular model and objective. Nearby vectors can indicate semantic similarity, but similarity does not establish factual support, authority, freshness or permission. Embeddings from different models are generally not comparable even if their dimensions match. Store model/version metadata and plan reindexing when it changes.

Cosine similarity measures angle; dot product also depends on vector magnitudes unless vectors are normalized. Approximate nearest-neighbor indexes trade some recall for speed. Evaluate retrieval with exact search as a reference on manageable datasets before tuning an ANN index.

```sql
SELECT id, text
FROM document_chunks
WHERE tenant_id = :tenant_id
ORDER BY embedding <=> :query_embedding
LIMIT 10;
```
This conceptual pgvector query puts tenant scope in the database query. Real ACLs may be finer than tenant membership. Approximate search and selective filters can reduce returned candidate counts; measure actual recall and inspect the chosen index strategy.

## Chunk around meaning
Fixed windows can split a rule from its exception or a table row from its headers. Overlap helps local continuity but can waste the retrieval budget on nearly identical fragments. Preserve headings, document IDs, version, access metadata and offsets. Compare chunking strategies using questions that require boundaries, tables and multi-part evidence.

## Use more than one signal when justified
Semantic search can miss exact product codes or legal clause numbers. Keyword retrieval can recover exact strings; hybrid retrieval combines different evidence and needs an explicit fusion/ranking policy. A reranker can improve ordering within the candidate set but cannot recover a relevant document that never entered it.

## Practical experiment
Build a small set of labeled questions before changing chunk size. Measure recall@k and inspect failures. Track irrelevant duplicates and context budget, not only one aggregate score. Mastery means explaining why a more expensive reranker cannot fix missing candidates or leaked access boundaries.
