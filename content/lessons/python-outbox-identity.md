## The idea in plain language

A retry is another attempt to deliver the same event. It must not create a new identity each time. Otherwise a consumer sees each attempt as new work and may apply the same effect again.

The lab uses the complete tuple (namespace, id, revision). A namespace separates scopes; a revision separates versions of one reading. The value belongs to the event payload. Changing the value under the same key is a conflict, not a reason to invent a fresh event key.

An event with value zero is still a real event. Code that treats zero like a missing INSERT result can count it incorrectly. Compare database RETURNING results with None explicitly. Repeated input can increase the receipt's observed and duplicate counts while creating only one intent for one full key.

Once an outbox row is acknowledged, recording the same fact again does not reset it to pending. Stable identity preserves the recorded delivery state. A matching historical fact without an intent can be adopted once. Different namespaces or revisions remain separate even when the short id is identical.

The supplied Event is frozen and strictly validates the same field rules as Datum. Frozen values help ordinary application code; they are not a security barrier against code that bypasses frozen fields. Revalidate and copy boundary values, and keep the expected claimed identity private while calling a publisher.

Identity is not permission. The surrounding application must authorize the namespace before invoking this library. A random token, page cursor or lesson completion cannot grant access. The earlier HTTP API retains its existing permission checks.

## Worked example

This local Python illustration explains one idea. The lab supplies actual database/process observations.

```python
first = ("scope", "a", 1)
retry = ("scope", "a", 1)
print(first == retry)
```

## Guided practice

Include namespace, id and revision. Changed facts under that key must conflict. A repeated attempt keeps its original identity.

## Independent practice

Implement or inspect the matching part of the lab. Run its public cases and save the actual before/after observations; explain one failure and one replay boundary.

## Check your work

Use one stable logical key across attempts. Zero is valid; None denotes no returned row. Label database skips, controlled models and limits honestly.

Continue to [Claim one pending event and confirm before acknowledgment](/lessons/python-outbox-claiming).
