Context is the space a supported model can use for input and output under a particular endpoint policy. A request can contain instructions, schema, user text, history, evidence and provider overhead. Counting only the visible question misses part of the request. Reserve output capacity as well; a request that fills all available space with input leaves no stated room for the answer. Decide what to reject or remove before sending, and make that decision visible instead of silently dropping meaningful input.

The offline lab uses a deliberately simple fixture rule: serialize the complete request as compact sorted UTF-8 JSON and count its bytes as input units. Add the configured output-unit reserve, then require the total to fit context_units. This is not a real tokenizer, a word count, or a universally conservative token estimate. The rule makes finite tests exact without pretending that different real models split text the same way. Production counters must match the supported model and include its actual framing and hidden overhead assumptions.

UTF-8 byte length differs from character count. A single visible character can take multiple bytes; JSON quoting, schemas and labels add more bytes. The small example below illustrates only that distinction. The installed request tests evaluate the full envelope, including the instructions and schema. They check an exact fit and one-unit overflow for both dialects. They also reject blank, wrong-type and overlong text before a provider call.

Context capacity and cost are related but different limits. A small enough request can still exceed the run's fictional credit budget. Conversely, free fixture rates do not make a request fit context. Keep both checks explicit. The lab preflights every prompt in the bounded batch before making any call, so a later invalid prompt does not leave earlier provider work partially completed. Its immutable copied request preserves the versioned envelope used for the admission decision.

## Guided practice

Predict the printed result, then describe the part of the real model boundary that this small illustration leaves untested.

```python
text = "é"
print(len(text.encode("utf-8")))
```

## Independent practice

Implement build_request. Count the complete fixture envelope, reserve output, and test exact fit/one-unit overflow plus multi-byte text. Confirm invalid later input prevents all provider calls.

## Check your work

Call these fixture units rather than real tokens. Explain which provider-specific counting and overhead assumptions would need independent verification.

Use the [Model contracts project](/projects#model-contracts). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
