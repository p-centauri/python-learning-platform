A loop that asks the model what to do next must have an application stop rule. The local lab permits one possible tool call per provider step and uses configured step, context, cost and local note limits. Every full serialized request includes the tool declarations and currently allowed observed results. Count all its UTF-8 bytes, reserve output units and fictional cost, and admit the request before attempting the call. These fixture units are not real model tokens or invoices.

One cooperative asyncio deadline covers the whole run, including every provider and tool wait. Starting a new full timeout for each step would let a many-step workflow exceed its intended lifetime. After one read consumes time, the next tool has only the remaining time. Refusal, incomplete output, invalid proposals, forbidden actions and uncertain tool failures stop the loop. The application does not automatically retry a side effect because the response looks inconvenient.

A provider timeout and a tool timeout are different observations. A provider may have unknown usage, so the lab retains its reservation. A tool can commit a note and then time out during the result-return wait. The report must not claim “no effect” or invent a successful returned result. Inspect the persisted receipt and explicitly reconcile using the same application operation ID under current approval. The demo observes one note remaining after this timeout and after a cancellation.

Cancellation cleanup is awaited, and external CancelledError propagates. There is no durable provider cost report after external cancellation. The receipt protects the local effect, not billing. Cooperative asyncio cancellation cannot interrupt arbitrary blocking SQLite calls or code that ignores cancellation. A tiny bounded local database makes these finite experiments practical; hard execution isolation, external quotas and production reconciliation require additional designs. Keep uncertainty visible instead of treating missing observations as proof.

## Guided practice

Predict the printed result, then explain which tool boundary this small illustration leaves untested.

```python
already_charged = 100
next_reservation = 300
maximum_cost = 350
print(already_charged + next_reservation <= maximum_cost)
```

## Independent practice

Test zero-call context/cost rejection, step limits, one deadline across multiple waits, provider cleanup, pre-effect timeout, post-commit timeout and propagated external cancellation.

## Check your work

Record actual calls and persisted effects. Distinguish unknown outcome from no effect, and state cooperative timeout/billing limits.

Use the [Authorized tools project](/projects#tools). Record commands, versions and failures. Reported tests and manual review remain separate from mastery.
