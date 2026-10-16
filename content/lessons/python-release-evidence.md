An operating runbook makes the order and owner visible. First stop all lab writers and consumers. Confirm the private disposable database and schema. Explicitly prepare migrations, compare metadata, check readiness and then start the installed loopback service. Observe permitted and rejected business calls. Stop and reap that process before another schema change.

The new release accepts delivery_004. Rolling back only its binary to the earlier service does not change that head: the old readiness still fails. Rolling back the schema has a different consequence. Choose a supported target only after naming what it destroys. delivery_003 retains service facts and timestamps, outbox, inbox and effects, but removes worker policies and job history. Those rows held attempt budgets, generations, deadlines and current state.

The larger service_002 rollback also removes outbox, inbox and effect rows. Service facts and timestamps remain, but the previous consumer receipt is gone. A retained broker Event can apply again after re-upgrade because the local deduplication history was erased. PostgreSQL rollback does not delete or restore an independent Redis payload. Pause replay until a separate recovery decision is made.

The CLI requires a named destructive target and --allow-loss before it connects. That flag acknowledges the documented choice. It is not a backup, authorization system or proof that stopping workers was done correctly. Re-upgrade creates empty lost structures; it does not restore past history. New startup at an old head must refuse, and explicit re-upgrade/check must precede restart.

## Try a small example

```python
retained = {"facts", "inbox"}
lost = {"jobs"}
print("inbox" in retained and "jobs" in lost)
```

Expected output: `True`.

## Guided practice

Use the prediction before running the snippet. Explain which owner keeps the state, then use the debugging checkpoint to choose a change at the failure boundary. The diagram and glossary describe the same sequence in words.

## Independent practice

Open the [Delivery release lab](/projects#python-delivery-release), download its starter after signing in and [submit evidence for review](/projects/python-delivery-release). Follow its RUNBOOK.md. Finish the three functions, install the eight-package chain and run 33 public cases: 15 offline and 18 requiring actual disposable PostgreSQL. Missing-store skips do not establish operating evidence. The demo also composes actual Redis redrive/pruning before the release and rollback.

Save actual head, finite HTTP statuses, process exit, retained/lost rows and pool cleanup. Include two useful regression cases of your own and a short explanation of the loss decision. Avoid raw exception strings and secrets in the artifact. Finite JSON events are diagnostic signals, not a full monitoring or trace platform.

Four review criteria are manual. Reported tests, reading, checklists and self/human review do not award practical mastery. This installed local rehearsal does not prove zero-downtime rollout, production backup/restore, broker failover or full academy deployment. Keep those limitations beside the evidence.

## Check your work

Explain the behavior in your own words, including a failure that the happy path misses. Compare your observation with the public tests and record what you actually ran. Revisit the short-answer recall with guidance closed; assisted and repeated answers remain different evidence.
