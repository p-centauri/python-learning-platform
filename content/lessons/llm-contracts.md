## Generation is not a database lookup
An LLM generates a continuation conditioned on context. A plausible answer may be unsupported, outdated or internally inconsistent. More confident wording does not make the underlying claim reliable. Design the application around observable contracts: which inputs are authoritative, what output schema is allowed and how claims can be checked.

Structured output can constrain shape. A schema-valid object can still contain the wrong account ID, an unsupported citation or a fabricated amount. Treat it as a typed proposal that must pass domain validation and authorization before it produces effects.

```json
{
  "intent": "summarize_spending",
  "period": "2026-08",
  "currency": "UZS"
}
```
The application must decide whether the period is valid, whose spending may be queried and how currency is represented. The model does not become an authority because its response parses successfully.

## Context is a scarce resource
A context window limits how much input and output can be considered in a request. Filling it with irrelevant history consumes cost and can obscure the evidence the task needs. Budget space for instructions, retrieved evidence, conversation and output. Record truncation decisions so a failure can be reproduced. Tokenization varies by model and language; characters are not an exact token count.

## Sampling and reliability
Lower sampling temperature can reduce variation for models that expose it, but does not guarantee correctness or identical outputs across infrastructure/model changes. Evaluate the specific model and endpoint capabilities. Retry only when useful: malformed output, refusal, timeout and an incorrect factual answer need different handling.

## Choosing a model
Use representative tasks, quality thresholds and latency/cost budgets. A larger model may improve difficult reasoning while making a simple extraction task unnecessarily slow. Fine-tuning can teach recurring behavior or format, but does not replace a fresh, access-controlled knowledge source.

## Practical checkpoint
Design an expense-classification response schema and list failures that schema validation cannot catch. Include abstention when confidence/evidence is inadequate. Mastery means treating generation, validation, authorization and evaluation as separate responsibilities.
