A query can run quickly and still answer the wrong question. Review meaning first: correct namespace, full keys, one contribution per fact, explicit empty/null behavior and newest-before-filter ordering. Then compare complete ordered outputs and inspect actual plans on a stated workload. This sequence makes a performance observation useful.

Open the [SQL query analysis lab](/projects#python-query-analysis), download its starter after signing in and [submit evidence for review](/projects/python-query-analysis). Finish summary.sql, history.sql and search.sql. The supplied typed Python functions own read-only transactions and return materialized copies; caller-owned engines remain available. SQL values are bound, with fixed query resources and no arbitrary SQL request endpoint.

The reporting schema is separate from the delivered service schema. Its notes reference the service's complete fact key. Fixture setup/mutations/index experiments are explicit trusted local work. They are not a new service migration and never run inside the academy API. The original source facts and source migration comparison are checked after the experimental indexes are removed.

Nine source/wheel packages are installed together outside source. Thirty-six public cases separate 23 offline boundary cases from 13 PostgreSQL cases. A missing disposable store causes explicit skips. The demo saves real joined/window/JSONB results, source compatibility, a 40,000-row workload, baseline/indexed plans, result equivalence and released pools. Skips, timeouts and fixture failures are not passing database evidence.

## Try a small example

```python
checks = {"same_results": True, "timing_observed": True}
print(checks["same_results"])
```

Expected output: `True`. This in-memory illustration is separate from database evidence.

## Try it in PostgreSQL

Run this literal example only on your disposable PostgreSQL store; the maintainer verifier evaluates it on PostgreSQL 17.

```sql
WITH versions(id,revision,value) AS (VALUES ('a',1,0),('a',8,2),('b',1,2)),
ranked AS (SELECT *,row_number() OVER (PARTITION BY id ORDER BY revision DESC) AS position FROM versions)
SELECT id,revision,value FROM ranked WHERE position=1 ORDER BY value DESC,id LIMIT 1;
```

The SQL returns a / revision 8 / value 2.

## Guided practice

Predict the small result before checking it. Use the second checkpoint to diagnose the query or evidence boundary. The diagram and glossary describe the same idea in simple words.

## Independent practice

Save your actual queries, command/output, report JSON and a short explanation of two regression cases you added. Include a direct-join fanout failure and an old-note/newest-revision failure, or equally useful independent cases. Explain what each test catches instead of copying its assertion text.

Interpret rare and wide predicate observations separately. Name cache/statistics/row-limit effects, index write/storage costs and any estimate mismatch. Per-statement lock/time limits are not a hard whole-job deadline. Separate calls have separate snapshots; a namespace parameter assumes prior authorization.

Four review criteria are manual. Reading, guided/checklist results, reported tests and self/human feedback never certify expert practical skill. This bounded rehearsal is not a whole service load test, production index rollout, arbitrary-query sandbox, backup/restore or full academy deployment. Keep limitations beside the evidence.

## Check your work

State the full scope/key, what each output row means and what the failure case proves. Record the commands you actually ran and any skipped cases. Explain the result in your own words before revisiting private recall with guidance closed.
