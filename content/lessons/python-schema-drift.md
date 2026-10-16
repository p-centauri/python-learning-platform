## The idea in plain language

The revision table is a receipt for migration work. It is not a live description of all database objects. Someone can remove an index or add a column after delivery_004 commits while leaving the revision unchanged.

inspect_state reports the current revisions. Its at_head property is true only for the single expected delivery_004 revision. The separate check function first requires that head, then asks Alembic to compare the database with combined service and delivery metadata. The lab enables type and server-default comparison.

The live cases remove a ready-job index, alter a default, add a column and add an unexpected table. Head remains true, but the autogenerate comparison detects the differences. Calling upgrade again at head does not repair them because there is no new revision to execute.

This comparison has limits. The pinned Alembic version does not establish CHECK expression correctness or data invariants. A separate live case drops the inbox value CHECK, inserts an invalid negative value and shows the comparison still passes. Successful comparison must therefore carry its exact scope, with reviewed migrations and independent invariant tests.

Compatibility is separate again. The earlier service's /ready route expects service_002 and returns 503 at the new head, although its business permissions and outputs remain unchanged. Select a compatible release and the new explicit readiness workflow before resuming traffic. This unit supplies that schema workflow; it does not claim a deployed application has already been upgraded.

## Worked example

This local illustration explains the idea. It does not run a database migration; actual store evidence comes from the lab.

```python
at_head = True
required_index_present = False
print(at_head and required_index_present)
```

## Guided practice

The revision is delivery_004, but a required index was removed. Which statement is correct? Explain why the documented boundary matters, then check the matching lab case.

## Independent practice

The autogenerate comparison passes after a CHECK was removed. What follows? Write your decision before checking the answer. Reproduce the relevant boundary in the disposable lab and save the observed revision, fields and error or result.

## Check your work

Revision bookkeeping can stay current while the actual schema changes. A useful comparison can still have documented blind spots. Keep head, drift, data validity and application compatibility separate. Label skipped store work as unevaluated; reported output and manual judgment do not award mastery.

Open the [Delivery migration lab](/projects#python-delivery-schema), download the starter after signing in, then [submit evidence for review](/projects/python-delivery-schema).

Next: [Keep migration failure inside one transaction](/lessons/python-migration-locks).
