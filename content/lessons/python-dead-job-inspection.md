## The idea in plain language

A dead job is work the worker has stopped trying. In this lab, **poison** means the caller classified an attempt as unsuitable to retry automatically. **Exhausted** means the saved attempt budget has run out. Neither state means the event was successfully delivered.

Start by inspecting, not by deleting the row. `inspect_dead` returns the complete Event, generation, reason and saved maximum. Namespace, id and revision identify the fact; value must match as well. For example, revision 1 with value zero is different from revision 2 with value nine. Keep both observations intact.

Inspection validates its namespace and an exact integer limit from 1 to 64 before connecting. It reads only unacknowledged dead jobs in that namespace, ordered by id and revision. Results are copied values, not live database objects. The function changes no job, policy or acknowledgment. A result of eight rows says only which eight rows this query observed. It does not prove there are no other failures.

A snapshot may become stale immediately. Another operator can retry a poison job, and the next worker claim can increase its generation. Therefore inspection is evidence for a decision; the mutation must check the current state again. Never use a saved Python object as permission to overwrite a newer attempt.

Diagnose the cause before choosing redrive. Record which dependency, input assumption or application bug was fixed. The library assumes the caller already has authority for the namespace. Its generation number is a concurrency guard, not a password. Keep private database errors and credentials out of submitted reports. The following local sorting illustration explains ordering only; the lab separately observes real PostgreSQL rows.

## Worked example

This is a local illustration. Actual store evidence comes from the lab.

```python
keys = [("a", 2), ("a", 1), ("b", 1)]
print(sorted(keys)[:1])
```

## Guided practice

Inspect two revisions of the same id, including value zero. Request limit=1 and then limit=8. Record the returned full keys and prove that inspection changed no database rows.

## Independent practice

Save a generation-1 snapshot, then let a second operator redrive and claim the job. Explain which field must fail when the old snapshot is reused.

## Check your work

Use the complete key, matching value and saved attempt fields. A bounded current read is not a global recovery conclusion; a later mutation must reject stale observations.

Continue with [Redrive a job without resetting its attempts](/lessons/python-guarded-redrive).
