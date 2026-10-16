## Two systems, two commit points
A worker consumes an event, writes PostgreSQL and acknowledges the broker. Those steps are not one atomic transaction. A crash after the database commit but before acknowledgement leaves durable business state and an unacknowledged delivery. The broker can redeliver it. Moving acknowledgement before commit replaces duplicates with possible lost work.

The useful goal is a business effect that is safe under repeated delivery. Store an inbox marker for a stable event identity in the same transaction as the effect:
```sql
BEGIN;
INSERT INTO consumed_events (consumer, event_id)
VALUES ('ledger-v1', :event_id)
ON CONFLICT DO NOTHING
RETURNING event_id;
-- Only if the insert returned a row:
-- apply the corresponding ledger mutation here.
COMMIT;
-- acknowledge after commit
```
The consumer name scopes deduplication to an independently meaningful handler. A duplicate insert waits for a competing transaction to finish; if that transaction rolls back, a subsequent attempt can apply the effect. Do not insert a durable marker in a separate transaction before the actual work.

## Ordering is a separate property
Deduplicating version 8 does not stop version 7 arriving after it. A state projection may need an aggregate sequence number and a conditional version update. A ledger that records independent additive entries needs a different invariant. Decide whether ordering is global, per entity or irrelevant; global ordering can unnecessarily constrain throughput.

## External effects reopen the boundary
An inbox table cannot atomically include an email provider or payment processor. Use a provider idempotency key, an outbox for intended work and reconciliation for unknown outcomes. Be precise about the guarantee: effectively-once business effects under stated assumptions, not magical exactly-once execution.

## Incident exercise
Draw a crash point before commit, after commit and after ack. For each, list which system remembers the event, whether it will retry and whether a duplicate effect is possible. Add a failing database transaction to verify that the inbox marker rolls back too. Observe deduplication counts and redelivery rates; a spike may reveal downstream latency or acknowledgement timeouts.
