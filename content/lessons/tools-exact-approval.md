Approval should describe one concrete action. “You may save this note” is incomplete when the actor, source or label can still change. The local lab binds approval to the policy version, tenant, actor, stable operation ID, tool name, note label and exact selected citation. Changing any of those action parameters requires a newly approved action. A model saying “already approved” cannot supply that approval.

The application helper computes a SHA256 digest over canonical action data. Canonical JSON keeps field ordering and byte representation stable, so the same action produces the same digest. This digest is not a signature or a password. Anyone who knows the data can calculate it. Authority comes from the trusted application callback containing an approval digest that the application actually granted. Never read that trusted value from a user prompt, retrieved document or model response.

The model call ID is intentionally excluded from approved action identity. Orchestration can lose a result and ask again; a model may then produce a different call ID for the same action. The application keeps the stable operation ID and canonical action unchanged. This allows a retry to reconcile with the saved receipt instead of producing a second note. A different label or source is not the same retry.

Even a newly granted approval cannot overwrite a previously committed operation with different content. That would turn an old retry key into a new mutation. The receipt detects this conflict separately from permission. For a genuinely new action, the application chooses a new operation ID and concrete approval. The lab uses a small local note to make the distinction observable; actual consequential services need their own user-facing approval record and policy. It does not claim a production signing or identity system.

## Guided practice

Predict the printed result, then explain which tool boundary this small illustration leaves untested.

```python
approved_label = "Review file cleanup"
proposed_label = "Send private files"
print(approved_label == proposed_label)
```

## Independent practice

Compare application approval against the complete canonical action. Test changed labels, sources, actors and operation IDs, plus a changed model call ID for an unchanged action.

## Check your work

State why a digest alone grants nothing and why a conflicting committed operation remains rejected after new approval.

Use the [Authorized tools project](/projects#tools). Record commands, versions and failures. Reported tests and manual review remain separate from mastery.
