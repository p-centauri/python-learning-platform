An index offers another way to find rows. A B-tree is useful for supported equality, ranges and ordering. Column order matters: this lab tests equality on namespace, then a value range, with id/revision as deterministic order fields. Its candidate is a B-tree on namespace, value, id and revision.

JSONB containment has a different access pattern. The experiment creates a GIN index using jsonb_path_ops on body for @>. This operator class supports the stated containment query; it is not the choice for every JSON operator, including key-existence needs. GIN does not provide the report's final ordering, so PostgreSQL may still sort.

A planner chooses using estimates, statistics and costs. ANALYZE collects statistics; it does not execute your SELECT or guarantee perfect estimates. A small table, common predicate, different order or expensive heap visits can make a sequential scan sensible. An index also costs space and work during writes. Do not turn sequential scans off to manufacture a result.

EXPLAIN shows the planned tree. EXPLAIN ANALYZE actually runs the query and adds observations. Only fixed SELECT queries run in the lab's read-only transaction. Do not accept arbitrary SQL from a browser or learner upload. Even a SELECT can do expensive work; a returned-row LIMIT does not cap every underlying scan.

Read each node's estimated rows, actual rows and loops. Actual row/time figures are per loop; account for loops when estimating volume. Parent/child cost and buffer figures overlap, so adding them double counts. Costs are planner units, not milliseconds. Shared buffer hits can reflect a warm cache rather than storage reads; an index-only scan can still need heap fetches.

## Try a small example

```python
estimated_rows = 100
actual_rows = 10
loops = 3
print(actual_rows * loops)
```

Expected output: `30`. This in-memory illustration is separate from database evidence.

## Try it in PostgreSQL

Run this literal example only on your disposable PostgreSQL store; the maintainer verifier evaluates it on PostgreSQL 17.

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT value FROM generate_series(1,3) AS value WHERE value=2;
```

The SQL returns an actual JSON plan whose root reports one output row; costs and timing vary.

## Guided practice

Predict the small result before checking it. Use the second checkpoint to diagnose the query or evidence boundary. The diagram and glossary describe the same idea in simple words.

## Independent practice

Run the deterministic fixture with 40,000 records and notes, 100 selective high values and ten rare kinds. ANALYZE first. Save baseline range/containment plans, create the two explicit experimental indexes, then save selective and wide-range plans. Verify identical ordered query results before discussing performance.

Record actual node/index names, estimates/rows/loops, root buffer counts, costs and execution time. If an index is not chosen, report that honestly and explain the workload; no exact plan name or timing threshold is a passing gate. Drop the fixture indexes afterward and verify original source metadata again.

The simple arithmetic prediction illustrates loops. The SQL example below runs a tiny SELECT through EXPLAIN ANALYZE on actual PostgreSQL, separately from the larger index experiment. Its variable costs/timing should not be memorized.

## Check your work

State the full scope/key, what each output row means and what the failure case proves. Record the commands you actually ran and any skipped cases. Explain the result in your own words before revisiting private recall with guidance closed.
