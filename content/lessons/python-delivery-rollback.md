## The idea in plain language

A downgrade can retain business facts while deleting the history that made delivery safe. Reverting delivery_004 to delivery_003 removes policy and job tables. Their leases, generations, retry schedule and terminal decisions disappear. The earlier outbox, inbox and aggregate still remain.

Reverting further to service_002 removes those outbox, inbox and effect tables too. Service namespace/id/revision/value/ingested_at rows remain unchanged. Delivery intents, duplicate receipts and aggregate state are lost. That is a destructive change even though the service still has its original facts.

The public wrapper requires the exact flag allow_loss=True before opening a connection. It refuses base and service_001. This makes the requested loss visible; it is not a backup, approval system or proof that rollback is safe for a running product. Use only the owned disposable rehearsal and pause writers and consumers.

Re-upgrade creates empty delivery history. A retained Redis entry with the same stable Event key can now apply again because its inbox receipt was deleted. The lab actually observes that behavior. A stable key protects replay only while the relevant deduplication history still exists.

Do not solve this by silently trimming the broker or automatically replaying every service row. Those are separate retention, recovery and business policies. Compare facts and delivery history at each boundary, record what was lost, and choose a compatible release before resuming processing. A failed downgrade also needs proof of rollback; the live suite adds a dependent table and observes all earlier drops roll back on failure.

## Worked example

This local illustration explains the idea. It does not run a database migration; actual store evidence comes from the lab.

```python
facts_retained, delivery_history_retained = True, False
print("facts retained; history lost" if facts_retained and not delivery_history_retained else "inspect")
```

## Guided practice

Which argument permits this lab's destructive delivery downgrade? Explain why the documented boundary matters, then check the matching lab case.

## Independent practice

The inbox was dropped, re-upgrade created an empty one, and Redis retains an old entry. Can that key apply again? Write your decision before checking the answer. Reproduce the relevant boundary in the disposable lab and save the observed revision, fields and error or result.

## Check your work

Only the explicit exact boolean flag permits the documented destructive targets. Deduplication depends on retaining the receipt, not merely on stable identity. Keep head, drift, data validity and application compatibility separate. Label skipped store work as unevaluated; reported output and manual judgment do not award mastery.

Open the [Delivery migration lab](/projects#python-delivery-schema), download the starter after signing in, then [submit evidence for review](/projects/python-delivery-schema).

Next: [Rehearse and review the installed migration lab](/lessons/python-migration-evidence).
