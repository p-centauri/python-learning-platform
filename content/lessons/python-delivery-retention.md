## The idea in plain language

Retention is a decision about what to keep and what to remove. A broker payload and a deduplication record serve different purposes. The payload lets a group replay transport history. The inbox key tells the local consumer that an Event has already been applied.

This lab removes only one explicitly selected broker payload. It keeps PostgreSQL facts, outbox intents, inbox keys, effects, policy and jobs. Removing those keys or resetting job generations would weaken replay safety. The earlier schema has no completion timestamp, so this lab does not pretend to know which work is older than a chosen number of days.

Before removal, read a supported envelope in the requested namespace. Require matching inbox and outbox values, producer acknowledgment and a done job. Hold shared database locks while the broker guard runs. Then the supplied Redis script checks the payload is unchanged, checks every current group has passed that id and has no pending reference to it, and removes the entry in the same atomic script. It accepts one to eight current groups. A lagging or pending group blocks removal; no groups also blocks it.

The script protects the current topology. Freeze group creation, destruction and cursor rewinds while selecting and pruning history. A group created tomorrow cannot read a payload removed today. That lost replay history is the reason for exact `allow_loss=True`; the flag is an acknowledgment of the boundary, not proof of operational safety.

The database and broker do not share a transaction. A broker deletion can succeed even if the later Python call or database transaction fails. Retry inspection of that exact id and preserve local history. The failure test observes this explicitly. Replaying the same Event at a new stream id remains safe for the retained local inbox; arbitrary external effects need their own contract. No bulk trim, TTL, age policy or backup guarantee is provided.

## Worked example

This is a local illustration. Actual store evidence comes from the lab.

```python
groups = {"effects": True, "audit": False}
print(all(groups.values()))
```

## Guided practice

Create an audit group that has not read the payload. Attempt pruning after the effects group completes. Then deliver and acknowledge audit and try again.

## Independent practice

Prune an eligible payload, append the same Event using a new stream id, and observe the effect count. Save before/after local rows and show that every retained key and generation is unchanged.

## Check your work

Pending and unread groups block. Successful pruning removes the payload only. The inbox preserves one local application; future groups lose access to removed history.

Continue with [Rehearse redrive, pruning and replay together](/lessons/python-recovery-evidence).
