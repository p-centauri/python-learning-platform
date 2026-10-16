A search question is data. It cannot grant a user a new role, select another tenant or turn a private document into public evidence. The application supplies the principal separately from the query text. In this lab the principal contains a tenant and allowed groups. Public chunks have no group restriction; restricted chunks require at least one matching group. This finite rule is a teaching contract, not a full login or policy service.

Validate the bounded corpus first. Next find the highest revision for each tenant and document across all rows. Only after that should you check activity and permissions. Suppose revision 1 was public and revision 2 became private. Filtering private rows first would make revision 1 look like the newest available row, exposing outdated public material. The correct result for a user without access is no hit from that document. The same no-fallback rule applies when the newest revision is inactive.

After choosing current revisions, apply tenant, active state, allowed groups and optional topic/document filters. Only eligible rows may enter the scoring function. Take the best k from this filtered set. Ranking everything and deleting private hits afterwards both processes forbidden text and can leave too few public results even when eligible candidates exist. A regression that observes calls to the scoring helper can detect this ordering mistake directly.

The current corpus is assumed to contain a coherent, complete current revision and consistent metadata supplied by the application. Removing the latest row without a tombstone could make an older row appear current. This lab does not implement atomic reindexing, deletion or database transactions. Later document-lifecycle work must preserve those facts. The report returns keys, offsets, digests and scores rather than raw private text, but safe response shapes alone do not prove every permission boundary is correct.

## Guided practice

Predict the printed result, then explain which retrieval boundary this small illustration leaves untested.

```python
allowed = {"ops"}
required = {"admin"}
print(bool(allowed & required))
```

## Independent practice

Implement retrieve using supplied eligible validation. Test a closest private hit, another tenant, latest-private/old-public revisions, inactive updates and metadata filters before scoring.

## Check your work

Explain trusted principal ownership and the complete-current-corpus assumption. Do not claim an entire production authorization system is verified.

Use the [Scoped retrieval project](/projects#retrieval). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
