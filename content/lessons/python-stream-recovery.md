## The idea in plain language

A dead consumer may leave entries pending. XAUTOCLAIM can assign sufficiently idle entries to a replacement consumer. Idle time gives a recovery policy, not proof that the original process is gone or stopped doing work.

The supplied helper requests one recovered message and returns a continuation cursor. Keep that cursor across bounded recovery calls so a scan can reach later pending entries. Starting over at 0-0 forever can revisit a bad early message and starve later work. No returned entry can mean none qualified in that scanned region, not that every pending entry disappeared.

Redis can report pending IDs whose payloads were trimmed or deleted. The helper exposes those deleted IDs. It does not invent their original Event or claim successful application. Retention must account for slow consumers and recovery needs; automatic trimming is deliberately absent from this unit.

Two separate authored processes exit with os._exit. After a broker AOF flush but before producer settlement, exit 91 leaves a pending producer lease and one stream entry. Observe database expiry, reclaim generation two and republish: two stream IDs produce one local effect. After a consumer commit but before XACK, exit 92 leaves one effect and one pending entry. Observe its broker idle time, reclaim it and acknowledge without increasing the effect count.

The parent observes actual tagged database and broker connections disappear before inspecting the committed state. Small sleeps pace observations instead of proving order. Another test actually restarts the owned broker with the same AOF volume and observes its retained entry and pending group state.

These are real worker exits and a controlled broker restart while PostgreSQL remains alive. They do not prove database power loss, broker failover, volume loss, backup recovery, fairness or exactly-once delivery.

## Worked example

This local illustration explains one boundary. Actual broker/database/process evidence comes from the lab.

```python
first_generation, reclaimed_generation = 1, 2
print(reclaimed_generation > first_generation)
```

## Guided practice

Check actual exit, pending work and idle or lease time. Preserve the scan cursor and stable Event key. Separate replay/restart evidence from power-loss claims.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation and explain the stable key, current transport state and failure boundary.

## Check your work

Idle ownership recovery cannot stop an older callback. Missing retained payload is a gap to report, not successful application. Label offline skips, modeled failures, actual process exits and controlled restarts honestly.

Continue to [Build and review the broker delivery lab](/lessons/python-stream-evidence).
