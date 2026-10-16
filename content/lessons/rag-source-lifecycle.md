A retrieval system needs rules for documents that change. A source can gain new text, move to a restricted group, become inactive or be deleted. Updating only its text leaves old vectors or permissions attached to new content. Publish the text, vectors, metadata, activity and access rules as one complete version. The lab uses a scoped tenant/document key and requires every meaningful change to advance its revision.

The local Index is constructed without opening a database. You explicitly initialize a separate SQLite file for the exercise; never use the academy database. Each operation opens and closes its own connection. A write starts one transaction, validates the existing state and proposed complete record, replaces the record and advances an index epoch. If a later SQL statement fails, the whole publication rolls back. The epoch identifies a changed snapshot, not the truth of its documents.

An exact replay of the same revision and content makes no change. A lower revision or different content at the same revision is a conflict. These rules make repeated input predictable without silently accepting contradictory facts. Tenant is part of the key, so two tenants can publish the same document ID independently. The exercise stores at most sixteen identities and sixty-four chunks; exceeding either cap fails the whole write.

Deletion keeps a tombstone: the document identity and new revision remain, but its text and vectors are absent. Without that marker, an old message could recreate supposedly deleted public content. Reopening the file must retain the deletion revision and reject old publications. A later explicit revision may restore the document. This verifies a bounded local lifecycle, not general distributed ingestion, embedding regeneration or production PostgreSQL operation. Keep the source publisher and its permission metadata under application control.

## Guided practice

Predict the printed result, then explain which evidence boundary this small illustration leaves untested.

```python
latest = {"guide": 2}
incoming = 1
print(incoming < latest["guide"])
```

## Independent practice

Implement publish using one index transaction. Verify complete update, exact replay, conflict, rollback and deletion/reopen/old-publication rejection. Keep the lab file separate from academy data.

## Check your work

Explain why deletion needs a retained revision and what the local SQLite experiment does not prove about distributed ingestion or production PostgreSQL.

Use the [Evidence answering project](/projects#rag). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
