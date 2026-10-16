## RAG is a pipeline, not a prompt trick
Retrieval-augmented generation introduces a source of evidence between a question and a generated answer. The pipeline can fail at ingestion, parsing, chunking, embedding, retrieval, ranking, context assembly or generation. Debugging only the final prompt hides the location of the actual failure.

```text
Question → authorized candidate retrieval → reranking
         → bounded evidence context → generation
         → citation/support checks → response or abstention
```
Preserve source IDs, versions, chunk offsets and permission metadata during ingestion. Query rewriting can improve search but must preserve the user's intent and authorization scope. Never trust a model-supplied tenant ID to decide access.

## Citations must support claims
A citation link proves that a source exists, not that it supports the claim next to it. Bind generated citations to allowed evidence IDs and verify that cited spans support material statements. An answer can cite a document correctly while misreading its exception. When evidence is missing or conflicting, state the limitation or abstain according to the product's risk profile.

## Access control is end to end
Filter before untrusted candidates enter model context. Carry authorization through retrieval, reranking, context caches and citation downloads. A cache keyed only by question can leak a response created for a different tenant. Include authorization-relevant identity/version in cache keys or avoid caching those results until a safe design is justified. Handle permission revocation and document deletion explicitly.

## Diagnose with paired evidence
If a golden supporting passage is absent from candidates, fix retrieval. If it is present but omitted from the context, examine ranking/budgeting. If it is in context and the answer is wrong, examine instructions, model behavior and support checks. Measure quality at each boundary to keep these causes distinguishable.

## Architecture exercise
Design a policy assistant where an employee changes teams. Trace the old document through the index, candidate cache, answer cache and citation endpoint. Explain how revocation propagates. Mastery means providing a measurable correctness and isolation argument, not assuming that adding citations makes hallucination impossible.
