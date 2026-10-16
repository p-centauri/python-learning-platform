A tool can succeed even when its caller never receives the result. Consider a note inserted just before the connection or task is interrupted. Retrying with a fresh identity can insert it again. The model's call ID is unsuitable as the only retry identity because the model may invent a new one each time. The application supplies a stable operation ID for one intended action.

The separate local SQLite database stores notes and operation receipts. One immediate transaction looks up the complete tenant, actor and application operation ID. If the receipt already has the same action fingerprint, return the existing note ID without another note. If the fingerprint differs, reject an operation conflict. If no receipt exists, check the note caps, insert the note and insert its receipt before committing. A late receipt failure must roll back the note too.

Scope is part of identity. Two actors can use the same operation string without sharing receipts. A duplicate at the note limit can replay its existing result, while a new operation must fail the limit. Reopening the database preserves receipts, so the protection does not disappear with a Python object. Replays still need current source access and exact approval; a saved receipt is not permission to disclose revoked content.

This transaction is possible because both local effects belong to the same SQLite database. It does not make a remote payment, email or HTTP request atomic with the receipt. Recording a local receipt after such an external effect leaves a failure window; recording it first can falsely claim completion. External services need supported idempotency, reconciliation and explicit uncertainty policies. The exercise calls its observed local behavior atomic replay, never universal exactly-once delivery. Retain that distinction when designing real tools.

## Guided practice

Predict the printed result, then explain which tool boundary this small illustration leaves untested.

```python
receipts = {"note-operation-1": 1}
retry_operation = "note-operation-1"
print(receipts[retry_operation])
```

## Independent practice

Implement same-action replay and conflicting-action rejection. Test reopen, changed model call IDs, actor scope, caps and a SQL failure after the note insert but before its receipt.

## Check your work

Show actual note/receipt counts. Explain why one local transaction cannot guarantee an external effect happened exactly once.

Use the [Authorized tools project](/projects#tools). Record commands, versions and failures. Reported tests and manual review remain separate from mastery.
