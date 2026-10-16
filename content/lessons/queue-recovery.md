## Acknowledgement transfers responsibility
A broker delivery remains recoverable until acknowledged according to the queue's semantics and durability configuration. Acknowledge before a durable business effect and a worker crash can lose work. Acknowledge afterward and a crash can produce redelivery. Prefer recoverable duplicates with idempotent effects for important jobs.

Retries need classification. A transient database outage may succeed later. Invalid input or a permanently unsupported schema will not become valid after ten retries. Separate these paths, cap attempts, add jitter and route poison messages to a visible quarantine with enough context for repair. A dead-letter queue without an owner or alert is just quieter data loss.

```python
# Conceptual worker boundary
try:
    apply_idempotent_effect(event)
except TransientFailure:
    retry_with_bounded_backoff(event)
except InvalidEvent:
    quarantine(event)
else:
    acknowledge(event)
```

## Cache failure should have a defined meaning
Cache-aside reads PostgreSQL on a miss and fills Redis with a TTL. A synchronized expiry can turn a quiet database into an overloaded one. Use jittered expirations, bounded refresh concurrency and appropriate stale-data policies. Do not let a cached authorization decision outlive revocation requirements without explicitly accepting that risk.

A Redis lock is not proof that only one process can ever execute. A paused holder can outlive its lease and resume after another holder acquired the lock. Use a random ownership token for safe release; critical downstream writes may need fencing tokens or a database invariant. A local lock does not coordinate replicas.

## Operational exercise
A downstream provider is down for five minutes and queue depth rises. Increasing workers may amplify the outage. Examine arrival rate, processing rate, retry rate, oldest message age and downstream limits. Choose backpressure, delayed retries or load shedding based on the business deadline. Mastery means explaining recovery and user-visible delay, not only the happy-path messages-per-second number.
