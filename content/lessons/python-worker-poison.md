## The idea in plain language

Some failures may be temporary. Others need a person or a changed system before the same event can succeed. A poison message is an event the current processing contract cannot handle successfully. Retrying it forever is rarely useful.

The lab has two explicit failure outcomes. Failure.RETRY requests the bounded schedule, while Failure.POISON quarantines the current job immediately. The stored reasons are finite labels, not copied exception messages that might contain private configuration.

Quarantine means state dead while the original fact, outbox intent and stable key remain saved. It does not mean the event was accepted. Its outbox row stays unacknowledged. This distinction matters when inspecting counts: pending intents can include quarantined jobs, so they are not all claimable now.

An exhausted attempt budget also quarantines with reason exhausted. The next claim may close up to 64 expired final attempts. An ordinary callback exception attempts to schedule a retry, then the run re-raises the same exception. If even that scheduling fails, the committed lease can expire. Abrupt process death follows the same recovery path without normal cleanup.

Recording an identical fact again must not secretly redrive a dead job. That would erase the attempt limit and make a repeated HTTP request an operational command. Future repair/redrive tooling needs authorization, an audit trail and a decision about preserving identity and previous acceptance. It remains outside this exercise.

A reviewer should inspect the reason, original value, attempted generations and destination behavior before repair. Do not turn quarantine into a success receipt. The finite public tests evaluate these local decisions; saved learner reports still require human review and do not certify reliability.

## Worked example

This small local illustration explains one idea. It does not evaluate the database or process boundary; use the lab for that evidence.

```python
state, acknowledged = "dead", False
print(state == "dead" and not acknowledged)
```

## Guided practice

Separate retryable and poison outcomes. Store a reason without inventing acceptance. Do not reset dead work on a duplicate record.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation, name the owner and time boundary, and explain one failure.

## Check your work

Quarantine preserves failed work without inventing acceptance. A duplicate record is not an authorized redrive command. Label controlled timestamp fixtures and actual process observations separately.

Continue to [Stop new claims and finish admitted work cooperatively](/lessons/python-worker-shutdown).
