## The idea in plain language

The producer and consumer do not share one transaction across PostgreSQL and Redis. The producer first saves a fact and outbox intent, then its leased worker sends an envelope to the broker. The consumer may apply that event later.

Redis XADD appends an entry and returns a stream ID. That reply by itself is not the disk-flush boundary this lab requires. The supplied adapter also calls WAITAOF with one local AOF flush and no replica requirement. It confirms the returned count before the publisher returns Accepted.

Both commands must use the same physical connection because the flush wait covers preceding writes on that connection. The adapter leases a dedicated connection from the borrowed client pool, executes the two commands and releases that connection. It leaves the caller's pool open. AOF is configured with appendfsync always; the owned broker uses a retained local volume for the controlled restart test.

Accepted then lets the existing worker finish its producer job and acknowledge the outbox. It means the stated broker boundary was confirmed. It does not mean the PostgreSQL consumer inbox or effect exists yet. A real test observes producer completion while the consumer application count is still zero.

If the append succeeds but its confirmation is lost or fails, the entry may already exist. A later attempt may append the same Event under another stream ID. Keep the stable fact key and let the consumer inbox arbitrate repeated effects. Do not claim a failed reply proves no append.

The demo verifies a controlled restart of this AOF broker. It does not prove hardware power-loss safety, replica failover, lost-volume recovery or exactly-once transport. Socket and flush-wait limits are not a hard total callback deadline.

## Worked example

This local illustration explains one boundary. Actual broker/database/process evidence comes from the lab.

```python
broker_accepted, consumer_applied = True, False
print(broker_accepted and not consumer_applied)
```

## Guided practice

Receive a transport entry ID. Check the local AOF count on that connection. Consumer effects remain a later boundary.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation and explain the stable key, current transport state and failure boundary.

## Check your work

Broker acceptance and the consumer database effect have separate boundaries. A failed response does not establish that the append never occurred. Label offline skips, modeled failures, actual process exits and controlled restarts honestly.

Continue to [Separate new messages from pending consumer work](/lessons/python-stream-groups).
