## The idea in plain language

Imagine worker A claims generation one, pauses, and loses its lease. Worker B later claims generation two. A wakes and tries to acknowledge the event. Accepting A's write would let an old owner change the replacement's job.

A fencing token is an increasing number used to reject older writes. This lab uses the generation stored on each job. A settlement must match the current generation, complete event key, payload, saved deadline and leased state. The deadline must still be live when PostgreSQL performs the guarded write. A stale settlement returns False and changes nothing.

The write must check time after any row-lock wait. Checking a Python timestamp before waiting is insufficient. Even a worker that has not been replaced loses settlement authority after expiry. Accepted changes the job to done and its outbox row to acknowledged in one transaction. A real CHECK failure on acknowledgment must roll both changes back.

Event identity stays namespace, id and revision. Generation identifies the reservation; it does not create a new fact. Returning a different value or event as acceptance must not authorize acknowledgment. The callback receives a separate validated Event copy, keeping its mutable tricks away from the private expected value.

The token protects this guarded database writer. It cannot stop a stale worker from sending an email or charging a card. Such a destination needs its own durable acceptance/idempotency or fencing contract. The existing local consumer protects its inbox and aggregate in one PostgreSQL transaction.

A generation number is not a password. A malicious caller could invent numbers; authorization belongs to the surrounding application. The lab assumes trusted local code and an already authorized namespace.

## Worked example

This small local illustration explains one idea. It does not evaluate the database or process boundary; use the lab for that evidence.

```python
current_generation, old_generation = 2, 1
print(current_generation != old_generation)
```

## Guided practice

Match the full key, value, generation and deadline. Reject an expired claim even after a lock wait. Job completion and outbox acknowledgment share a transaction.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation, name the owner and time boundary, and explain one failure.

## Check your work

The guarded database write must match the current generation. Local fencing protects the guarded database operation. Label controlled timestamp fixtures and actual process observations separately.

Continue to [Save retry times and cap delivery attempts](/lessons/python-worker-backoff).
