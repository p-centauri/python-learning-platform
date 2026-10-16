## The idea in plain language

A retry should answer two questions: when may this job run again, and how many attempts remain? Retrying immediately forever can consume the worker and hide a persistent failure.

The lab persists an immutable Policy for each namespace. It includes lease milliseconds, maximum attempts and one delay for each possible retry. Later workers must use the same policy. They cannot silently extend the attempt limit after a restart.

Each committed claim consumes one attempt, even if the process dies before sending anything. For an explicit retry outcome, settlement saves ready and next_at using the settlement database time plus that attempt's delay. A future next_at prevents early admission. The worker returns; it does not hold a connection or sleep inside the transaction until that time.

After a crash, no explicit failure settlement exists. The next claim therefore uses the saved lease deadline plus that attempt's delay. A real process test observes expiry using PostgreSQL before reclaiming. Other scheduling tests deliberately edit owned fixture timestamps; label that controlled model separately from actual waiting.

When the last claim expires or its retry fails, the job becomes dead with reason exhausted. It keeps its original fact and unacknowledged intent for inspection. No further claim is admitted under this contract. Stable identity lets a replayed accepted event meet the same consumer inbox key.

A small delay schedule is backoff, not proof of fairness or protection against synchronized fleets. This sequential lab has no random jitter, global capacity limit, lease renewal or automatic SQL retry. A count bound cannot interrupt a blocked callback. Operational scheduling and service capacity need their own evidence.

## Worked example

This small local illustration explains one idea. It does not evaluate the database or process boundary; use the lab for that evidence.

```python
maximum, attempts = 3, 3
print(attempts >= maximum)
```

## Guided practice

Every reservation consumes one attempt. Use the database time and the stated delay. Do not admit another attempt after the limit.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation, name the owner and time boundary, and explain one failure.

## Check your work

A persisted future schedule must prevent early admission. The saved count is bounded across process failures. Label controlled timestamp fixtures and actual process observations separately.

Continue to [Keep poison messages visible without endless retries](/lessons/python-worker-poison).
