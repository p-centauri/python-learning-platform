# Fixture model contract v1

These are two invented protocols, not an emulation of any named provider API. The configured revision is fixture-model-2026-10, prompt triage-v1, schema triage-schema-v1. Providers are trusted configured adapters with a borrowed async Transport. Transport.send accepts immutable request bytes and returns untrusted bounded response bytes. No transport/network resources are acquired by the run.

## Request and context

Exact ModelConfig and Limits values are frozen copies. Identifiers are lowercase ASCII letters/digits/underscore/hyphen, 1..64 characters; dialect is message-v1 or completion-v1. Context 1..16384 units, output 1..1024 units, fictional input/output rates 0..1000 integer credits per unit. Booleans are not integers here. Prompts are nonempty non-whitespace strings <=4096 UTF-8 bytes. The run accepts an exact tuple of <=8 strings and validates every prompt before calling.

Canonical sorted compact UTF-8 JSON includes model, prompt_version, a supplied schema and either role-labelled messages/max_output or separate instructions/input/output_limit. The full serialized byte count is the fixture input_bound. Require input_bound + output_units <= context_units. Do not count only user text or silently truncate. Real deployments need a model-specific counter, full provider overhead/output policy and independently verified capabilities; this fixture makes no such claim.

## Responses

Message variant has exactly:

```json
{"model":"fixture-model-2026-10","status":"complete","text":"{\"queue\":\"python\",\"summary\":\"Check the traceback\",\"needs_human\":true}","refusal":null,"usage":{"input":10,"output":20}}
```

Status complete requires text and null refusal. Status refused requires null text and nonempty refusal. Status incomplete requires null refusal and partial text or null. All provided text is <=4096 UTF-8 bytes; refusal/partial text is discarded after validation and is never parsed as a complete proposal.

Completion variant has exactly model_id, stop, result, meter. Stop done requires result with content only; refused requires refusal only; limit requires partial only. Meter uses the same exact input/output fields. All model identifiers must match the configured revision; mixed variants, extra fields, unknown stop values and malformed/duplicate JSON are invalid.

Response bytes are exact bytes <=16384, explicitly UTF-8, with no duplicate keys or non-finite JSON constants. Meter fields are exact integers: input 0..input_bound and output 0..output_units. The fixture trusts reported usage only within these bounds; it does not prove a remote invoice or hidden usage is correct. Complete text is strict JSON with exactly queue (python/database/http), nonempty summary <=240 UTF-8 bytes and an exact boolean needs_human. No coercion, fenced-output repair or generated authorization is supported.

## Run and ledger

Limits: 1..8 max_steps, 0..100000000 max_cost fictional credits, 1..10000 timeout_ms. Each attempt reserves input_bound*input_rate + output_units*output_rate before awaiting. If the reserve will exceed the remaining local cost budget, no call is made. Known fully validated usage settles to input*input_rate + output*output_rate and releases unused credits. Invalid/provider-error/timeout outcomes retain the full reserve; known refusal/incomplete usage settles but stops. Every attempted call counts as a step. No retry is automatic.

One monotonic deadline begins after preflight and shrinks across the provider-call loop. Finite synchronous work/cleanup may exceed it; cooperative timeout is not a kill switch. External CancelledError propagates after cooperative transport cleanup; there is no durable cancellation ledger or remote rollback promise. Reports identify provider/model/prompt/schema, fixed stop kind, charged credits and copied step usage/decisions without raw requests, refusal text or exceptions. A valid queue never authorizes business effects. Fresh-run limits are not persistent account quotas or a real-money ceiling.
