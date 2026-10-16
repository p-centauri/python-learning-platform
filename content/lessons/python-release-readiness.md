A health endpoint and a readiness endpoint answer different questions. Liveness asks whether the process can answer. Readiness asks whether the dependencies this application needs are currently usable. If PostgreSQL is unavailable, /health can still return 200 while /ready returns 503. That difference helps the operator decide where to investigate.

The earlier ingestion application correctly expects its own service_002 schema. The delivery extensions advance the same chain to delivery_004, so its old /ready now fails. Editing that old package would change an already published contract. Instead, create a parent FastAPI application with compatible /health and /ready routes, then mount the unchanged service at /. Its business paths, authentication, strict fields and commit-before-success behavior remain in place.

The new check requires exactly one expected head and queries the required service and delivery table columns with LIMIT 0. These queries test whether the shapes needed by this release exist without reading all rows. A head label alone is insufficient: somebody could drop or rename a required column without changing the version table. The supplied live fixture demonstrates that failure in its generated schema.

The check owns a fresh read-only PostgreSQL transaction. It sets a 250ms lock limit and 1000ms statement limit, releases its connection and returns a finite reason. Pool wait and connection setup have their own bounds. These are individual limits, not a hard total HTTP deadline. Do not hide programming errors as success.

## Try a small example

```python
heads = ("delivery_004",)
expected = ("delivery_004",)
print(heads == expected)
```

Expected output: `True`.

## Guided practice

Use the prediction before running the snippet. Explain which owner keeps the state, then use the debugging checkpoint to choose a change at the failure boundary. The diagram and glossary describe the same sequence in words.

## Independent practice

Implement assess and test a correct head, old head, missing required column, actual refused connection and exhausted pool. Observe 200 to 503 to 200 after the fixture changes and restores its version value. The version edit is a test fault in an owned schema, never an operating instruction.

Prepare and check migrations separately before startup. Autogenerate comparison can find modeled drift but does not fully check CHECK expressions or existing data. LIMIT 0 does not validate all constraints, indexes or data either. Record those limits instead of calling this a complete schema audit.

This API uses PostgreSQL for its routes. It does not automatically enqueue work, so its readiness does not claim Redis health. Workers and broker checks belong to their separate owner. A ready response is neither authorization nor a reservation: the next write still needs permission and can fail before commit.

## Check your work

Explain the behavior in your own words, including a failure that the happy path misses. Compare your observation with the public tests and record what you actually ran. Revisit the short-answer recall with guidance closed; assisted and repeated answers remain different evidence.
