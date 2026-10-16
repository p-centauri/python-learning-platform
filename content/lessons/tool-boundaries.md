## A tool call crosses a trust boundary
A model-produced tool name and JSON arguments are untrusted inputs. Route only allowlisted names, validate arguments against a strict schema and authorize the requested operation using the real authenticated principal. Never accept a model-provided role or tenant as proof of authority.

```python
class CreateExpense(BaseModel):
    model_config = ConfigDict(extra='forbid')
    account_id: int
    amount_minor: int = Field(gt=0)
    currency: Literal['UZS', 'USD', 'RUB']
```
This schema is useful, but the service still checks account ownership, currency compatibility, business limits and required approval. Keep money in an exact representation; do not ask the model to decide the trusted ledger mutation directly.

## Approval belongs to a specific action
For consequential actions, show the user a concrete action and bind approval to its canonical parameters and identity. If the amount, recipient or account changes, prior approval must not silently authorize the changed action. Record who approved what, when and under which policy version.

## Retrying the action
A tool call can succeed while its result is lost. Use a stable operation ID across orchestration retries and enforce idempotency in the application service. A model-generated new call ID on every retry is not sufficient business identity. Preserve the original operation through checkpoints and reconciliation.

## Tool results are also untrusted
A document-search result may contain instructions telling the model to send secrets to another tool. Keep tool-output content in a data role and enforce permissions outside the model. Return structured errors that distinguish invalid input, forbidden operations, transient failures and unknown outcomes. Redact secrets from traces while retaining enough context to debug failures.

## Workflow or agent?
A request to fetch account totals and produce a chart often has a fixed sequence. A deterministic workflow is easier to test and bound than an open-ended agent loop. Add autonomous planning only where task variability justifies the new failure modes and budgets.

## Mastery exercise
Trace an expense creation through parsing, ownership checks, approval, idempotency, transaction and audit record. Inject a malformed amount and a forged tenant ID. Show that both are rejected even if the model insists they are valid.
