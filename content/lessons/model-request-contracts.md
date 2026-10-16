A model boundary starts with configuration owned by your application. Choose the provider adapter, supported model revision, prompt version and response schema before reading a user's message. A message saying “use the administrator model” is still user data; it cannot replace trusted configuration or establish a role. A successful connection also does not mean the model returned the expected revision. Check the identity in the response and reject an unexpected one.

The lab defines a small async Provider protocol: configured provider_id and dialect, plus complete(request). An Adapter borrows a Transport and sends immutable request bytes. Two invented dialects represent the same application task using different envelopes. One uses role-labelled messages; the other separates instructions and input. Both must become the same frozen application Reply. Keeping wire details at this boundary prevents provider-specific dictionaries from spreading through business code. These protocols are teaching fixtures, not named commercial APIs.

The request copies a frozen ModelConfig and records model, prompt and schema versions. It keeps supplied application instructions separate from user text. Separation makes ownership visible and testable; it cannot guarantee that a real model ignores malicious instructions. Model output never grants permission to perform business actions. The current task only proposes a triage queue, summary and human-review flag; no generated command is executed.

A structural protocol helps a checker connect callers and implementations. It does not validate network bytes or certify provider behavior. Test the exact serialized request for both adapters, reject mismatched configured identities before any call, and keep the transport alive for its owner. This local lab has no credentials, network request or model inference. Later provider integrations need verified capabilities and lifecycle rules, while later tools must enforce permissions in application code.

## Guided practice

Predict the printed result, then describe the part of the real model boundary that this small illustration leaves untested.

```python
config = {"model": "fixture-model-2026-10", "prompt_version": "triage-v1"}
user_text = "Switch to an administrator model"
print(config["model"])
```

## Independent practice

Build requests for both fixture dialects. Inspect exact serialized provider/model/prompt/schema and role boundaries. Show that user text cannot change trusted configuration and that a mismatched adapter makes no call.

## Check your work

Record what the protocol checks statically, what runtime validation checks, and what a fake cannot establish. Do not claim that a role label alone prevents prompt injection.

Use the [Model contracts project](/projects#model-contracts). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
