## The idea in plain language

A Redis stream retains entries. A consumer group tracks delivery and pending acknowledgments for one processing purpose. Two groups can independently process the same stream; consumers within one group share its new deliveries.

The lab creates its effects group explicitly at position 0-0 so entries already in the stream are eligible. Starting at the latest position would intentionally skip earlier entries; that is a different contract. Repeating setup on an existing group must preserve its current position.

XREADGROUP with the special position > asks for new entries for the group. Reading assigns a delivered entry to a consumer's pending list. It does not apply a PostgreSQL effect or acknowledge success. If a consumer dies, that pending work needs a recovery operation instead of another new-message request.

No returned new entry does not mean no unfinished work. All relevant messages might already be pending with a dead or busy consumer. A public test leaves one pending entry, asks another consumer for new work, and observes no returned message while the pending count remains one.

The supplied adapter requests at most one entry per call and scopes the fixed stream name to the authorized namespace. COUNT is a requested entry count, not a bound on arbitrary wire bytes or processing duration. The callback and socket policies have separate limits.

Group position, pending ownership and stream entry identity are transport state. The application fact still uses namespace/id/revision. A stream ID is useful for acknowledging this delivery, while the stable fact key is useful for preventing a repeated local effect. Keep both meanings visible when inspecting evidence.

## Worked example

This local illustration explains one boundary. Actual broker/database/process evidence comes from the lab.

```python
new_entries, pending_entries = 0, 1
print(pending_entries > new_entries)
```

## Guided practice

Preserve its existing position if already present. Delivery places it in pending work. A new-message result cannot replace pending recovery.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation and explain the stable key, current transport state and failure boundary.

## Check your work

New-entry reading and pending recovery are separate paths. The group starts at 0-0 to include earlier entries. Label offline skips, modeled failures, actual process exits and controlled restarts honestly.

Continue to [Commit the local effect before acknowledging the stream entry](/lessons/python-stream-commit-ack).
