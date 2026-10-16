## The idea in plain language

Complete the five earlier packages and this migration extension. Build real source archives and wheels, then install all six in a fresh Python environment. Run copied tests outside the source trees so a local import path cannot hide missing migration resources.

Implement upgrade, downgrade and check. The provided owner configures the connection, transaction, local SQL limits and advisory lock. The packaged revisions supply immutable history; combined metadata describes expected service and delivery structures without mutating the previous service metadata.

The 44 public cases separate 25 offline checks from 19 live cases. Missing PostgreSQL skips migration behavior; missing Redis skips the broker composition case. Report those skips honestly. Offline boundary validation cannot evaluate a database transaction, DDL wait, installed broker or destructive rollback.

The actual installed demo starts from timestamped service_002 facts. It preserves them through upgrades, explicitly adopts old matching facts, delivers through the completed leased worker and real broker, detects a missing index while head stays current, and observes both rollback boundaries. Re-upgrade has empty history, so the same old key can apply again. Save actual JSON, installed versions and exact old API permission/readiness observations.

Four manual criteria separate preserved/versioned schema, head/drift/compatibility, failure/loss boundaries and installed observations. Add regressions and explain what the evidence cannot prove. The academy serves the starter and stores manual evidence; it never executes this package. This finishes a bounded migration rehearsal. Bounded retention/redrive is published in the next module; release compatibility, deeper SQL/API teaching and applied AI remain planned; passing tests and reported checklists do not establish expertise.

## Worked example

This local illustration explains the idea. It does not run a database migration; actual store evidence comes from the lab.

```python
offline_cases, live_cases = 25, 19
print(offline_cases + live_cases)
```

## Guided practice

All offline tests passed and PostgreSQL was missing. What is evaluated? Explain why the documented boundary matters, then check the matching lab case.

## Independent practice

Why run copied tests outside the source tree after installing the wheel? Write your decision before checking the answer. Reproduce the relevant boundary in the disposable lab and save the observed revision, fields and error or result.

## Check your work

Skipped live checks cannot establish store behavior. A source import can hide an incomplete wheel; clean installed evidence checks the artifact. Keep head, drift, data validity and application compatibility separate. Label skipped store work as unevaluated; reported output and manual judgment do not award mastery.

Open the [Delivery migration lab](/projects#python-delivery-schema), download the starter after signing in, then [submit evidence for review](/projects/python-delivery-schema).

Continue with [Inspect dead jobs before changing them](/lessons/python-dead-job-inspection).
