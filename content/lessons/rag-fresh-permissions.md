Generation takes time. A user can change teams, a document can become restricted, or an administrator can delete a source while the provider is waiting. Permission checks performed only before retrieval are therefore incomplete. The application supplies a current-authority callback. The answer stage calls it before using the Bundle and again after receiving a valid proposal. A changed tenant or group snapshot discards the proposed text and citations.

Document state is refreshed too. The Bundle records the index epoch and the exact prepared evidence. Before the call, reprepare and compare the complete plan; stale or forged bundles cannot send evidence to the provider. After generation, read current source state and reprepare again. An update, ACL change or deletion that changed the epoch invalidates the plan. A second Index owner can publish during the controlled call, making this timing boundary testable with real local storage.

This lab is conservative: any changed index epoch invalidates the Bundle, even an unrelated document update. That may create avoidable abstentions but simplifies the stated finite freshness contract. A more selective invalidation design needs an explicit correctness argument. The current-authority callback and source metadata must be trusted application inputs. A model response saying “the user is now an administrator” never changes either.

Do not hold a database connection across the provider await. Each read is a short owned snapshot. A final check establishes the allowed state at that observation point; it cannot prevent future changes after the answer returns. When revisiting an old citation, resolve it again under current authority. The project intentionally has no answer cache, because safe scope and invalidation rules are additional work. Citation/source checks establish current local provenance, not a complete production authentication or distributed revocation system.

## Guided practice

Predict the printed result, then explain which evidence boundary this small illustration leaves untested.

```python
before: tuple[str, tuple[str, ...]] = ("alpha", ("ops",))
after: tuple[str, tuple[str, ...]] = ("alpha", ())
print(before == after)
```

## Independent practice

Test permission changes and source update/delete/ACL changes during generation using a refreshed authority callback and a second Index owner. Verify stale output is discarded and old citations no longer resolve.

## Check your work

State the final observation-point guarantee, conservative global epoch invalidation and trusted-authority assumptions. Do not promise permanent permission or safe answer caching.

Use the [Evidence answering project](/projects#rag). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
