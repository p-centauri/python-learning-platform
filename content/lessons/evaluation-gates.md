## “Looks better” is not a release criterion
A prompt that improves three demos can degrade uncommon languages, long documents or refusal behavior. Start with representative cases and expected properties before tuning. Include ordinary tasks, difficult edge cases, empty evidence, adversarial documents and important user segments. Separate development examples from a held-out evaluation set.

Store case IDs, inputs, authorized context, expected evidence, expected behavior and review rationale. Version the dataset and run configuration together with prompt, model, retrieval and tool policy. A reproducible failure is more useful than a score without provenance.

## Measure the right boundary
Retrieval recall@k asks how much labeled relevant evidence appeared among k retrieved candidates. Answer correctness asks whether the response is right. Groundedness asks whether claims are supported by the supplied context. Tool-selection accuracy and argument validity are separate from successful business execution.

```python
# Example release gate, thresholds are product-specific
assert new.tenant_leaks == 0
assert new.refusal_regressions == 0
assert new.retrieval_recall_at_10 >= baseline.retrieval_recall_at_10
assert new.p95_latency_ms <= latency_budget_ms
```
These assertions need adequate data and uncertainty analysis; tiny datasets do not prove a zero incident rate. Report sample size and failure examples alongside metrics. Use exact checks for schema, permissions and deterministic facts where possible.

## Judges are instruments, not authorities
An LLM judge can scale review but may share biases with the model under test and prefer fluent verbosity. Validate its rubric against human labels, blind comparisons where practical and inspect disagreements. Never let a judge override deterministic security failures. Keep adversarial instructions in candidate answers from changing the grading policy.

## Tradeoffs and mastery
Quality, latency and cost can move in different directions. A release decision needs explicit thresholds for critical behaviors and acceptable tradeoffs for others. Segment results by language, task type and evidence difficulty so an aggregate improvement cannot hide a serious regression. Mastery means producing a small reproducible evaluation pipeline and defending what its metrics do—and do not—establish.
