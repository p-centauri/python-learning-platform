## The idea in plain language

An ordinary exception usually runs context-manager cleanup. A process exit can skip that cleanup completely. The lab therefore starts a separate authored worker process and uses os._exit at three precise boundaries. PostgreSQL stays running while each worker disappears.

Before producer commit, the child inserts a reading and intent but exits inside the transaction. The parent observes that the child's database connections have closed. Neither row becomes committed. Recording again and delivering afterward produces one effect.

After producer commit, the child exits before any delivery. The parent sees one reading and one pending intent. A restarted worker claims that saved intent and delivers it. The work is stored in the database rather than a lost process-local queue.

After consumer commit, the child exits inside the publisher before the producer can acknowledge. The parent sees one applied effect and one pending intent. Restart delivers the same event again. The inbox recognizes the duplicate, leaves the effect count at one and allows acknowledgment to commit.

The parent polls actual pg_stat_activity until the tagged child's connections disappear, then reads committed state. Short sleeps only pace those observations. A timed sleep by itself would not prove cleanup or a crash boundary. Child exit codes and before/after state are saved as evidence.

These are real worker process exits. They are not database power loss or backup recovery tests. The disposable maintainer database uses tmpfs and is removed afterward. A separate lost-response test injects a modeled callback failure after an actual consumer commit; label that model honestly. Neither fixture proves exactly-once transport, arbitrary external effects or production durability.

## Worked example

This local Python illustration explains one idea. The lab supplies actual database/process observations.

```python
deliveries, applications = 2, 1
print(deliveries > applications)
```

## Guided practice

Terminate the separate trusted worker process. Wait for actual child connection disappearance. Preserve one effect despite repeated delivery.

## Independent practice

Implement or inspect the matching part of the lab. Run its public cases and save the actual before/after observations; explain one failure and one replay boundary.

## Check your work

Replay the stable key; the inbox prevents a second local effect. Name the actual failure boundary and surviving store. Label database skips, controlled models and limits honestly.

Continue to [Build and review the durable outbox lab](/lessons/python-outbox-evidence).
