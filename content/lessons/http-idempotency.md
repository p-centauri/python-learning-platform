## A timeout is missing knowledge
A payment API can commit a payment and lose the response. The client observes a timeout while the server observes success. Retrying with a new operation identifier can create a second payment. The application needs an identity for the intended operation that survives transport retries.

Require an idempotency key scoped to the authenticated caller and operation. Store a canonical request hash with that key, state and the stable result. Enforce uniqueness in PostgreSQL. Two requests that race to insert the same key must converge on the same operation. A check-then-insert without a unique constraint is another race.

```sql
CREATE TABLE idempotency_records (
  tenant_id bigint NOT NULL,
  operation text NOT NULL,
  key text NOT NULL,
  request_hash text NOT NULL,
  status text NOT NULL,
  response jsonb,
  PRIMARY KEY (tenant_id, operation, key)
);
```

## The state machine matters
A matching completed record returns the recorded result. A matching in-progress record returns a documented pending response or waits within a bounded budget. Reusing the key with a different request hash is a conflict. Store the domain write and result record in one database transaction where possible. An external provider requires its own idempotency boundary and reconciliation for ambiguous outcomes.

## Retry is a resource policy
Retry selected transport failures and documented retryable responses. Respect Retry-After where provided, apply exponential backoff with jitter, and cap both attempts and total elapsed time. A retry at three layers can amplify load multiplicatively during an outage. Assign one layer responsibility for the overall retry budget. A timeout should leave enough budget for cleanup and a useful error response.

## Tradeoffs and traps
GET is defined as safe; GET must not perform payments simply because clients readily retry it. PUT's idempotent semantics do not mean every implementation is correct. POST can provide application-level idempotency with a documented key contract. Define retention for keys: expiring a record can allow a delayed retry to become a new operation.

## Practical checkpoint
Sketch the sequence for two simultaneous identical requests and a third request with the same key but a different amount. Explain every response and the unique constraint involved. Mastery means handling uncertainty, concurrency, tenant scope and retention together.
