A join combines rows that match a condition. If one reading has two notes, joining them produces two rows containing the same reading value. Adding that value afterward adds it twice. Start by naming the unit of your report: one stored revision, one item, one note or one namespace. These are different counts.

The service identifies a reading by namespace, id and revision. All three fields must match when joining its notes. Joining only id can connect another namespace or a different revision. The reporting schema uses the same complete foreign key, so a note cannot point to a nonexistent revision. That constraint supports identity; it does not grant authorization to the caller.

For a total over all stored revisions, first group notes by the complete key. Join that one-row-per-key result to the facts. Each fact now contributes its value once, while a separate count can show how many facts have notes. SUM(DISTINCT value) is not a repair: two different facts may legitimately have equal values.

A LEFT JOIN preserves a source with no facts by creating a row whose right side is null. COUNT(*) counts that row, so use COUNT(record.id) for actual records. SUM over no matching values is null; COALESCE makes the report's empty total zero. An existing empty source should return a zero summary, while an absent source returns no summary. Filtering a right-side field in WHERE can remove the null-extended row; put a match restriction in ON when you intend to preserve it.

## Try a small example

```python
facts = [("a", 0), ("b", 7)]
notes = {"a": ["first", "second"]}
print(sum(value for _, value in facts))
```

Expected output: `7`. This in-memory illustration is separate from database evidence.

## Try it in PostgreSQL

Run this literal example only on your disposable PostgreSQL store; the maintainer verifier evaluates it on PostgreSQL 17.

```sql
WITH readings(id,value) AS (VALUES ('a',0),('b',7)),
notes(id,label) AS (VALUES ('a','first'),('a','second'))
SELECT r.id,r.value,count(n.label) AS notes
FROM readings r LEFT JOIN notes n ON n.id=r.id
GROUP BY r.id,r.value ORDER BY r.id;
```

The SQL returns a / 0 / 2 notes and b / 7 / 0 notes.

## Guided practice

Predict the small result before checking it. Use the second checkpoint to diagnose the query or evidence boundary. The diagram and glossary describe the same idea in simple words.

## Independent practice

Implement summary.sql in the starter. Test zero values, equal values in different facts, two notes on one fact, a missing note, an empty existing source and a completely absent source. Insert the same id in another namespace and show that it cannot change the authorized scope's counts.

Compare a deliberate faulty direct join with your corrected report on the disposable store. Record the changed count and explain its cause. Keep permission checks in the calling application; validating a namespace's spelling is not an access check. Every read owns a fresh read-only transaction and materializes results before releasing its connection.

The small Python example counts original facts. It illustrates the intended unit, rather than simulating PostgreSQL. The SQL example below shows actual outer-join behavior on literal rows. These finite examples do not prove every possible data distribution.

## Check your work

State the full scope/key, what each output row means and what the failure case proves. Record the commands you actually ran and any skipped cases. Explain the result in your own words before revisiting private recall with guidance closed.
