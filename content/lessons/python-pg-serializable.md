## The idea in plain language

A multi-row rule can fail even when every individual row is valid. Consider an append-only admission rule: allow at most one record in a dedicated namespace. Two transactions each read zero records and choose different keys. Uniqueness alone permits both keys; a stable snapshot alone does not encode the shared rule.

PostgreSQL SERIALIZABLE requires successfully committed transactions to have results consistent with some serial ordering. It may abort a transaction with 40001 when the observed dependencies cannot satisfy that condition. Stronger isolation does not mean every transaction succeeds, and it does not turn remote calls into database effects.

The lab starts two dedicated SERIALIZABLE connections. Both read zero before either admission. One transaction commits an admission and the other gets a real serialization failure. A fresh transaction reads the rule again and sees one admission, so its correct decision is to skip. Replaying just the failed INSERT would ignore the decision that motivated it.

This experiment does not change the earlier ingestion service's READ COMMITTED contract or invent a permanent one-admission business requirement for that API. It uses an explicitly named disposable fixture to teach dependency reasoning. The bounded delivery wrapper remains READ COMMITTED; a SERIALIZABLE workflow needs a whole transaction callback that reevaluates its own reads and decisions.

Hold results provisionally until the transaction commits. A calculation from an aborted transaction cannot be published as a final answer. 40001 is evidence of an aborted serialization attempt, while a communication failure around commit can have unknown outcome. Their responses need different policies.

The Python example illustrates rereading a decision input only. Actual separate-connection experiments establish the SQLSTATE and stored admission. Passing one finite fixture does not prove all business invariants, workload fairness or performance.

## Worked example

This local Python illustration explains one idea. The PostgreSQL lab supplies the actual database observations.

```python
fresh_count = 1
action = "skip" if fresh_count else "admit"
print(action)
```

## Guided practice

Explain the shared rule, the competing decisions and why a fresh read can change the correct action.

## Independent practice

Run serializable_gate and record one commit, actual 40001 and the fresh skip decision. Contrast row uniqueness with the cross-row rule.

## Check your work

Do not blindly replay a last statement or publish data from an aborted transaction.

Continue to [Bound retries by failure class and transaction ownership](/lessons/python-pg-retry-policy).
