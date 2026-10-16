GROUP BY reduces several rows into a group result. A window function keeps each row and adds a value calculated using related rows. This makes it useful for revision history: show the original revision, its previous value and a running total without throwing away row identity.

LAG(value) OVER (ORDER BY revision) finds the prior row in revision order. The first row has no prior value, so its previous value and delta are null. A prior zero is different: the next value minus zero is still a valid result. Revisions can have gaps, so previous means the previous stored row, not necessarily revision minus one.

For a general multi-item query, partition by the complete item identity, namespace and id. This lab's history query scopes to one namespace/id before the window, so that partition is already fixed. Order by revision. The revision key is unique in that scope; elsewhere, tied order values need a deterministic tie breaker.

Use SUM(value) OVER (ORDER BY revision ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) for an explicit running sequence. A default RANGE frame can include peer rows with equal order values. Choosing a frame tells the reader what the calculation includes; final ORDER BY tells them which order the results display. These are separate jobs.

Compute ROW_NUMBER over descending revisions to identify the newest one. Apply output LIMIT after calculating the windows over the full history. Otherwise a truncated history can incorrectly mark an old row newest. These are observed values in one statement, not a permanent claim about revisions a later writer may add.

## Try a small example

```python
values = [0, 7, 2]
running = 0
for value in values:
    running += value
print(running)
```

Expected output: `9`. This in-memory illustration is separate from database evidence.

## Try it in PostgreSQL

Run this literal example only on your disposable PostgreSQL store; the maintainer verifier evaluates it on PostgreSQL 17.

```sql
WITH revisions(revision,value) AS (VALUES (1,0),(3,7),(8,2))
SELECT revision,value,lag(value) OVER (ORDER BY revision) AS previous,
sum(value) OVER (ORDER BY revision ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM revisions ORDER BY revision;
```

The SQL previous values are null, 0, 7; running totals are 0, 7, 9.

## Guided practice

Predict the small result before checking it. Use the second checkpoint to diagnose the query or evidence boundary. The diagram and glossary describe the same idea in simple words.

## Independent practice

Implement history.sql. On revisions 1, 3 and 8 with values 0, 7 and 2, report previous values null, 0 and 7; deltas null, 7 and -5; running totals 0, 7 and 9. Mark only revision 8 newest, even when the caller requests only the first ascending output row.

Test a single row, missing id, another namespace with the same id and the result limit. Explain why a result-row cap does not bound all database scan/sort work. A fresh READ COMMITTED read has one statement's view; separate report calls do not share one snapshot automatically.

Keep these calculations in SQL rather than fetching every revision into Python. The typed wrapper returns copied values and closes its connection. The Python running-sum illustration is useful for prediction; the SQL example is separately run on PostgreSQL by the trusted verifier.

## Check your work

State the full scope/key, what each output row means and what the failure case proves. Record the commands you actually ran and any skipped cases. Explain the result in your own words before revisiting private recall with guidance closed.
