## The dual-write gap
An order endpoint commits an order, then publishes OrderCreated. If it dies between those steps, the order exists but fulfillment never hears about it. Publishing first reverses the inconsistency: fulfillment can receive an event for an order that later rolls back. No ordering of two independent commits removes both failure windows.

Record the order and the intention to publish in one PostgreSQL transaction:
```sql
BEGIN;
INSERT INTO orders (id, status) VALUES (:order_id, 'accepted');
INSERT INTO outbox (event_id, aggregate_id, type, payload)
VALUES (:event_id, :order_id, 'OrderCreated', :payload);
COMMIT;
```
A relay reads committed outbox rows, publishes them and records delivery. Polling is a simple starting point; change-data capture is another approach with a larger operational footprint. The outbox is not the event bus. It is durable evidence that publication is still required.

## Publication can still repeat
A relay can publish successfully and crash before marking the row sent. It republishes after restart. Consumers must be idempotent. Stable event IDs must survive relay retries. Marking sent before publication risks losing the event entirely.

Keep claim transactions short. If multiple relays use SKIP LOCKED, define recovery for a relay that crashes after claim. Bound retention and monitor oldest unpublished event age, queue growth, failures and time to business completion. A low queue depth is insufficient if one critical event is permanently stuck.

## Contracts and simpler alternatives
Version event payloads and distinguish facts from commands. Avoid serializing an entire ORM object with private fields or unstable structure. If work is purely local and can safely happen within one transaction, a service call may be simpler than adding a broker and outbox. If delayed work is dispensable, a best-effort task may be sufficient—but name that weaker guarantee explicitly.

## Design exercise
An order requires stock reservation and a confirmation email. Define transaction boundaries, event identity, retry behavior and a dead-letter/reconciliation path. Explain which effects are atomic, which are eventual and how the system handles duplicate delivery. A senior design makes the remaining failure modes inspectable instead of hiding them behind a pattern name.
