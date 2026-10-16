## The idea in plain language

An outbox is a table of work that still needs delivery. If you save a reading, commit, and only then add its event, a process can stop in the gap. The reading survives but nothing tells a worker to deliver it. Adding the event first creates the opposite risk: a worker may deliver a fact that never committed.

Put the fact and its outbox row in one database transaction. Both become committed together, or neither does. In this lab, record owns a new Session and inserts the source, reading and intent before committing. A late changed-value conflict rolls back all new rows in that batch. Previously committed rows remain intact.

The earlier ingest function already owns its transaction and returns after commit. Calling it and then writing an outbox row cannot create this shared boundary. The extension therefore implements its own explicit transaction using the same prior models and strict value rules. It leaves the earlier package and HTTP routes unchanged.

A matching older reading may have no intent because it came through the earlier API. The new record function adopts that requested fact by adding its intent once. This is an explicit choice, not an automatic historical sweep. Counts distinguish observed input, newly inserted readings, duplicates and newly enqueued events.

Schema setup is explicit too. Complete the prior service_002 migration, then install the supplied additive tables once in a disposable schema. Import and requests never run this DDL. Its one-time setup is a teaching boundary; production migration and drift integration need later work.

## Worked example

This local Python illustration explains one idea. The lab supplies actual database/process observations.

```python
facts, intents = 1, 1
print(facts == intents)
```

## Guided practice

Bound the strict batch before database work. Keep all new rows in one owned transaction. A late failure rolls back the whole new batch.

## Independent practice

Implement or inspect the matching part of the lab. Run its public cases and save the actual before/after observations; explain one failure and one replay boundary.

## Check your work

One transaction must save both the fact and intent. Keep the batch atomic; committed history remains. Label database skips, controlled models and limits honestly.

Continue to [Keep event identity stable across delivery attempts](/lessons/python-outbox-identity).
