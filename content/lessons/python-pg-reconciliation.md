## The idea in plain language

Reconciliation checks what is stored when a response did not establish a reliable outcome. It is a read with a stated meaning, not an automatic repair. The lab compares namespace, id, revision and value for each unique requested key. It never searches by id alone, overwrites a conflicting fact or treats valid syntax as permission.

reconcile validates/copies the bounded request before SQL, owns one fresh read transaction and selects only the requested complete keys within its namespace. matched_keys counts distinct keys whose values match, even when the submitted batch repeats an identical key. missing contains absent expected facts; conflicts contains expected facts whose stored values differ. Conflict takes priority, then missing, otherwise complete. Empty input is complete with zero matched keys.

Complete means every requested key/value fact was observed. It does not prove that a particular earlier transaction committed: a different writer may have stored identical facts. Counts from a lost receipt cannot be reconstructed as original inserted/duplicate counts. The observation supports a semantic fact check, not historical attribution.

Missing means a key was absent in that read's view. An in-flight writer may commit immediately afterward. The supplied real experiment reads missing while another transaction owns an uncommitted fact, then complete after that writer commits. Absence therefore does not prove rollback or authorize blind replay. A later application policy needs appropriate timing, stable identity and permission checks.

The acknowledgment-loss case deliberately commits actual data and then injects a modeled response failure. The wrapper stops after one attempt; reconciliation sees the committed fact. This shows policy behavior around real persisted state without claiming a real broken-network commit incident. Keep modeled faults and observed database failures distinct in your report.

The function does not provision sources, mutate rows or grant namespace access. A trusted caller must enforce authorization before using it. The existing API still checks its own permissions; the extension does not add an endpoint or change that boundary. Recovery across process crashes, durable receipts/outbox and external effects belong to the following units.

## Worked example

This local Python illustration explains one idea. The PostgreSQL lab supplies the actual database observations.

```python
facts = [("a", 1), ("a", 1), ("a", 2)]
print(len(set(facts)))
```

## Guided practice

Distinguish observed complete/missing/conflict facts from proving a specific transaction outcome.

## Independent practice

Implement the full-key scoped read. Run repeats, zero values, revisions, other namespaces, conflicts and in-flight/after-commit observations.

## Check your work

A missing read is not rollback proof; reconciliation stays read-only and does not award replay permission.

Continue to [Competing-transaction evidence and the recovery lab](/lessons/python-competition-evidence).
