A release factory is a resource boundary. It receives validated settings, creates its own engine and builds the application. Creating the engine should not connect to PostgreSQL. Importing the package should be quiet. Neither import, factory construction nor a request should run migrations automatically.

The lifespan owns the next phase. Before its yield, it makes a fresh readiness check. Only a successful check starts admission. An old schema or missing dependency refuses startup. After yield, the owner stops admission and disposes its engine. A finally block also handles startup failure. Construction errors before returning the application need their own cleanup because the caller has not received the ownership handoff yet.

The parent application owns this lifecycle. The mounted service borrows the engine and does not own a second lifespan cleanup. TestClient must be used as a context manager to exercise startup and shutdown. A request against an unstarted application must not accidentally grant business admission. Returning a release and then abandoning it is not a tested shutdown procedure; run it with its owning lifespan.

The stop event is a one-way local flag. It makes /ready fail and rejects subsequent business work with 503. /health remains available. It has no public endpoint for strangers to change. A request already admitted can continue: a gate cannot undo a database commit or interrupt arbitrary synchronous Python code.

## Try a small example

```python
running = True
stopping = True
allowed = running and not stopping
print(allowed)
```

Expected output: `False`.

## Guided practice

Use the prediction before running the snippet. Explain which owner keeps the state, then use the debugging checkpoint to choose a change at the failure boundary. The diagram and glossary describe the same sequence in words.

## Independent practice

Implement create_release and verify construction failure, rejected startup and normal shutdown each dispose once. Keep the old application's permission checks and public response fields. Return no-store on both operational and business responses.

Run the installed TCP case, not only TestClient. Start one owned loopback server, observe readiness and authenticated access, send SIGTERM, wait for the process and inspect tagged database connections. A port selection race must fail cleanly rather than stopping a different process. Cleanup is owned by the fixture, even after test failure.

The supplied Uvicorn command uses a three-second graceful budget. That is cooperative shutdown evidence, not a hard bound on every synchronous callback. A test needing kill as fallback has not passed its graceful assertion. Stop and reap all lab writers/workers before schema changes; this unit does not implement overlapping zero-downtime releases.

## Check your work

Explain the behavior in your own words, including a failure that the happy path misses. Compare your observation with the public tests and record what you actually ran. Revisit the short-answer recall with guidance closed; assisted and repeated answers remain different evidence.
