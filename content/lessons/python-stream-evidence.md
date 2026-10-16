## The idea in plain language

Complete the four earlier local packages and this extension. Build real source archives and wheels, install all five in a fresh environment, and run copied tests outside their source trees. The lab pins redis-py 6.4.0 and uses an owned Redis 7.4.2 broker alongside PostgreSQL 17.

Implement three functions: encode, decode and deliver. The supplied adapter handles dedicated connection ownership and raw broker replies. Its lower-level redis-py command boundary is narrowed and then validated at runtime; an annotation alone does not make a server reply trustworthy.

The 74 public cases separate 59 offline checks from 15 live checks. Without both configured stores, live cases explicitly skip. Offline success is useful evidence for envelopes and protocol ordering, but it cannot evaluate AOF flush, pending reclaim, real constraints or process recovery.

The maintainer verifier owns a password-protected loopback broker, a generated AOF volume, resource limits and a temporary database. It removes only those owned resources. Learner configuration must also point at explicitly disposable stores; no FLUSHDB or shared production restart is permitted by this exercise.

Save the actual demo JSON and parse it back. It records a completed producer while the consumer effect is absent, duplicate stream deliveries with one application, both child exits, recovery and a controlled broker restart. Keep installed distribution versions and earlier service 401/403/200 permission evidence. Add regressions for an unknown schema and acknowledgment before effect commit.

Four manual criteria separate envelopes/scopes, broker acceptance/ownership, consumer/recovery correctness and installed observations. Reported output, checklists and reviews do not award mastery. This finishes a bounded broker continuation, while operational migration/retention/redrive, deployment, deeper SQL/API work and applied AI still remain. The academy never executes this downloaded or submitted package inside its API.

## Worked example

This local illustration explains one boundary. Actual broker/database/process evidence comes from the lab.

```python
offline_cases, live_cases = 59, 15
print(live_cases > 0)
```

## Guided practice

Use all five completed local wheels. Report skips and named restart/crash boundaries. Keep finite checks and expertise separate.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation and explain the stable key, current transport state and failure boundary.

## Check your work

Skipped broker/database work remains unevaluated. Reported results and manual judgment remain separate from mastery. Label offline skips, modeled failures, actual process exits and controlled restarts honestly.

Open the [Broker delivery lab](/projects#python-stream-delivery), download its starter after signing in, then [submit work for review](/projects/python-stream-delivery).

Next: [Give delivery tables an explicit revision history](/lessons/python-delivery-revisions).
