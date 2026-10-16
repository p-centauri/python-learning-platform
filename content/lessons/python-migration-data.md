## The idea in plain language

Adding a delivery table does not mean every old fact should be sent again. A service may already contain the value zero, several revisions of one identifier and real ingestion timestamps. An additive migration should preserve those rows exactly while creating the new structures.

The rehearsal begins with two timestamped service_002 facts. It compares namespace, identifier, revision, value and ingestion time before and after every upgrade. Counting two rows alone would miss a changed value, swapped revision or overwritten timestamp.

The outbox starts empty. After migration, the completed record function can explicitly adopt matching existing facts and enqueue their stable identities. That is a business decision outside the schema migration. A matching adoption does not replace a fact; a changed value under the same key conflicts.

Keep migration work separate from the ingestion request. Imports and requests must not create tables or silently replay history. Pause writers and delivery workers while rehearsing the change, then choose when a compatible application resumes them. An advisory migration lock only coordinates callers that use it; it does not pause those other processes.

The example below copies a small value to explain preservation. It is not a database migration test. The actual lab uses PostgreSQL and observes all columns through separate calls. Save those observations rather than replacing them with a successful-looking row count. This is also why an existing fact and a pending delivery must remain different records.

## Worked example

This local illustration explains the idea. It does not run a database migration; actual store evidence comes from the lab.

```python
before = ("scope", "a", 1, 0, "2020-01-01")
after = tuple(before)
print(before == after)
```

## Guided practice

An upgrade keeps the row count but changes zero to one. Is that data preservation? Explain why the documented boundary matters, then check the matching lab case.

## Independent practice

Should the additive migration automatically enqueue every old service fact? Write your decision before checking the answer. Reproduce the relevant boundary in the disposable lab and save the observed revision, fields and error or result.

## Check your work

Preservation includes key, value and timestamp, not only the number of rows. Schema structure and a decision to deliver old facts are separate changes. Keep head, drift, data validity and application compatibility separate. Label skipped store work as unevaluated; reported output and manual judgment do not award mastery.

Open the [Delivery migration lab](/projects#python-delivery-schema), download the starter after signing in, then [submit evidence for review](/projects/python-delivery-schema).

Next: [Check the schema beyond its recorded head](/lessons/python-schema-drift).
