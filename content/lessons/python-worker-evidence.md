## The idea in plain language

Begin with the three completed local dependencies: service, competing ingestion and durable outbox. Build their wheels, implement this extension and build its source archive and wheel. Install all four in a fresh environment and run copied tests outside the source tree.

The supplied schema.sql and py.typed must exist in the installed package. Imports must stay quiet, with no database setup or signal changes. The explicit teaching setup adds worker_policy and delivery_job after the previous schema. It is one-time disposable DDL, not production migration or drift integration. The earlier HTTP routes and namespace permissions remain unchanged; POST still does not automatically enqueue.

The public suite separates offline boundary checks from actual PostgreSQL checks. Offline skips are honest but do not test leases, constraints or recovery. Save the actual installed demo JSON and parse it back. Installed distribution versions must come from real metadata, not a source-only fallback invented for a report.

Two authored subprocesses exit without Python cleanup: after the committed claim, and after the consumer commit before settlement. Observe their tagged database connections disappear, observe database expiry, then reclaim generation two. Both restarts preserve one local inbox/aggregate application despite replay.

Also preserve stale rejection, saved backoff, finite attempts, poison inspection, real acknowledgment rollback, separate worker claims, released pools and actual SIGTERM evidence. Add regressions that would catch an old-owner write and a premature retry. Explain that a settlement report includes retry and poison decisions, not just accepted events.

Four manual criteria separate reservations/fencing, schedules/quarantine, admission/shutdown and installed evidence. Checklists and reported tests do not increase mastery. Broker/delivery-schema evolution, production migrations/retention/redrive, release operations and applied AI remain later units. Worker exits while PostgreSQL remains running do not prove power-loss recovery or expert readiness.

## Worked example

This small local illustration explains one idea. It does not evaluate the database or process boundary; use the lab for that evidence.

```python
passed, skipped = 35, 24
print(skipped > 0)
```

## Guided practice

Run outside all four source trees. Save actual reclaims, quarantine and SIGTERM results. Separate finite checks, reported evidence and expertise.

## Independent practice

Implement or inspect the matching lab contract. Save an actual before/after observation, name the owner and time boundary, and explain one failure.

## Check your work

Explicit skipped integration work remains unevaluated. Stored output and manual judgment remain separate from mastery. Label controlled timestamp fixtures and actual process observations separately.

Open the [Leased worker lab](/projects#python-leased-worker), download its starter after signing in, then [submit work for review](/projects/python-leased-worker).

Continue to [Read supported event versions without changing the fact](/lessons/python-event-envelopes).
