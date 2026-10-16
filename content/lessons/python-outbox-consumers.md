## The idea in plain language

Repeated delivery is expected around a missing acknowledgment. The consumer needs a rule that recognizes the same event and protects its effect. Remembering a key only in memory is not enough when the process restarts.

The lab's inbox stores each complete event key and value. For a new key, consume inserts the inbox row and increments the namespace's aggregate total and application count. These writes share one transaction. A successful result comes only after both commit.

If the inbox insert commits first and the effect fails later, a replay can mistakenly skip a missing effect. If the effect commits first and the inbox fails later, replay can apply it again. The shared transaction removes these two local database gaps. A supplied real CHECK failure demonstrates that neither inbox nor aggregate survives that failed transaction.

A repeated key with the same value confirms acceptance and leaves the aggregate unchanged. A repeated key with a different value raises ConflictingEvent. The consumer compares the persisted payload rather than silently accepting the key alone. Separate revisions and namespaces apply independently; zero still counts as one application even though it adds nothing to the total.

This demonstration protects one PostgreSQL database effect. It does not make an email, payment or arbitrary callback duplicate-safe. A real external service needs its own durable idempotency/receipt contract, and a broker adapter needs a defined acceptance boundary.

The producer and consumer own independent Sessions and commits. The consumer cannot use the producer's open transaction as proof of independent acceptance. The first unit uses a trusted local PostgreSQL sink to make this boundary observable; a real broker remains later work.

## Worked example

This local Python illustration explains one idea. The lab supplies actual database/process observations.

```python
keys = {("scope", "a", 1)}
keys.add(("scope", "a", 1))
print(len(keys))
```

## Guided practice

New and repeated complete keys have distinct outcomes. Increment the aggregate in the same transaction. Conflicting repeats preserve the original effect.

## Independent practice

Implement or inspect the matching part of the lab. Run its public cases and save the actual before/after observations; explain one failure and one replay boundary.

## Check your work

Commit the inbox and local effect together. Stable identity must preserve the same fact. Label database skips, controlled models and limits honestly.

Continue to [Observe real worker exits and replay committed work](/lessons/python-outbox-crashes).
