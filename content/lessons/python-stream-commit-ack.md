## The idea in plain language

A stream acknowledgment tells the broker that this group no longer needs to keep the entry pending. It is not the transaction that applies the application effect. The order between those operations matters.

First validate the envelope and scope. Then call the prior consume function, which commits its inbox key and local aggregate effect together. Only after that commit should the consumer send XACK for the delivered stream ID. If the database effect fails, keep the entry pending so the failure remains recoverable.

Acknowledging first creates a loss window: the process can die after XACK and before applying the effect, leaving no pending delivery to recover. Committing the effect first creates a repeat window instead: the process can die before XACK while its database effect already exists. Stable identity and the transactional inbox make that later replay safe for this local effect.

Two stream entries can carry the same Event. They can even use different supported envelope versions. Their transport IDs differ, but consume sees the same namespace/id/revision and unchanged value. It confirms the repeated fact without increasing the aggregate again. A changed value under that key raises ConflictingEvent and retains pending work.

XACK removes a pending reference. It does not delete the retained stream payload. A zero acknowledgment count means that this call removed nothing; another consumer may already have acknowledged it. That count alone does not prove whether an effect happened.

Pending ownership is not a fencing lock. An old consumer may still run after another consumer claims the entry, and XACK does not require the current owner token. This lab protects the local database effect through its inbox. An email, payment or arbitrary external callback still needs its own acceptance/idempotency policy.

## Worked example

This local illustration explains one boundary. Actual broker/database/process evidence comes from the lab.

```python
delivery_ids = {"1-0", "2-0"}
application_keys = {("scope", "a", 1)}
print(len(delivery_ids) > len(application_keys))
```

## Guided practice

Reject unsupported or wrong-scope payloads. Repeated stable facts preserve one local effect. Remove pending only after local acceptance.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation and explain the stable key, current transport state and failure boundary.

## Check your work

The inbox and effect share the original commit. Stream retention and pending acknowledgments are separate state. Label offline skips, modeled failures, actual process exits and controlled restarts honestly.

Continue to [Reclaim pending entries and observe real crash windows](/lessons/python-stream-recovery).
