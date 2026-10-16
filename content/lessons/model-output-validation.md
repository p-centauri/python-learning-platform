Provider responses have more states than “a useful answer arrived.” A completed response can contain invalid JSON or an invalid domain value. A refusal may be a valid provider outcome rather than broken formatting. An incomplete response can end halfway through an object. These states need different handling. Do not parse a refusal or unfinished prefix as a completed business proposal, and do not hide missing information by repairing arbitrary generated text.

The decoder accepts bounded exact UTF-8 bytes and rejects duplicate keys, non-finite JSON constants, extra fields and unknown variants. It verifies the configured model identity and exact usage integers. Message-style status fields and completion-style stop/result fields normalize into complete, refused or incomplete. Mixed content/refusal fields are invalid. Refusal and partial text are bounded then discarded; the Reply has no Decision for them. Their raw text is not included in the run report.

Only complete text is decoded as a triage proposal. It must have exactly queue, summary and needs_human. Queue belongs to the supplied finite domain, summary is nonblank and byte-bounded, and needs_human is an exact boolean. The string “false” is not false. Ordinary coercion or Python truthiness can accidentally turn wrong input into accepted data, so the boundary checks current types rather than relying on annotations. Fenced JSON and trailing text are rejected instead of silently corrected.

Passing these checks still does not prove that the summary is true, that the queue is useful, or that anyone is permitted to perform a resulting action. The lab intentionally stops at a frozen proposal. Business authorization and later quality evaluation remain separate. Keep this distinction in your independent regression and review note: identify whether a case establishes parsing, shape, domain, identity, permission or semantic accuracy. A green schema test demonstrates only the boundaries it actually exercised.

## Guided practice

Predict the printed result, then describe the part of the real model boundary that this small illustration leaves untested.

```python
def is_boolean(value: object) -> bool:
    return type(value) is bool

print(is_boolean("false"))
```

## Independent practice

Implement decode_reply for both exact formats. Test complete/refused/incomplete, duplicate keys, wrong revision, mixed fields, fenced JSON, extra authority fields and string booleans. Keep non-complete Decisions absent.

## Check your work

Demonstrate that an accepted object can still be wrong or unauthorized. The decoder must not execute or treat generated fields as authority.

Use the [Model contracts project](/projects#model-contracts). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
