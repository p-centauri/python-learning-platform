## The idea in plain language

Redrive means deliberately asking the worker to try a failed job again. It starts with a diagnosed cause and an explicit decision. A button or script should not make poison disappear merely by restarting attempts from zero.

The function requires exact `approve=True` and an exact inspected `DeadJob`. It revalidates the copied Event and attempt fields before connecting. Only a poison job with remaining saved attempts is eligible. Exhausted jobs stay terminal. Keeping that boundary makes the attempt budget meaningful and avoids an endless sequence of supposedly fresh first attempts.

The database change matches the Event namespace, id, revision and value, the observed reason and generation, and the saved maximum. It also requires the current job to be dead and its outbox intent to remain unacknowledged. A matching job becomes ready now with reason retry. Generation and policy are unchanged. A later worker claim increases generation as usual.

One conditional UPDATE decides whether the current row still matches. Two concurrent requests using the same snapshot can produce one success and one refusal. Repeating a successful request also refuses. If a newer attempt has already failed, the old generation does not match even though its Event is unchanged. The earlier leased-worker settlement guards continue to reject an old lease before and after the next claim.

The operation owns a short PostgreSQL transaction and releases it before returning. A database failure rolls back the local change. It does not automatically retry. `True` means the job is committed as ready; it says nothing yet about broker acceptance or a consumer effect. Keep those later receipts separate. This unit assumes the existing worker policy and publisher model; mixing older unfenced publishers remains unsupported.

## Worked example

This is a local illustration. Actual store evidence comes from the lab.

```python
generation, maximum = 1, 3
ready_generation = generation
next_claim = ready_generation + 1
print(ready_generation, next_claim, maximum)
```

## Guided practice

Quarantine generation 1 as poison, save its snapshot, redrive it and repeat the request. Record ready generation 1, claimed generation 2 and the repeated refusal.

## Independent practice

Run two redrive calls from separate threads using the same snapshot. Then try to settle the old lease. Record actual results and explain why no attempt counter was reset.

## Check your work

Expect one concurrent success, one refusal and stale-lease settlement refusal. An exhausted request must retain its Event, generation and budget.

Continue with [Prune broker payloads while keeping replay history](/lessons/python-delivery-retention).
