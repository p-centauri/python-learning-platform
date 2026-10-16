# Delivery recovery lab

Implement **inspect_dead**, **redrive** and **prune** in `operations.py`. The fixed SQL schema,
Event/Lease/Policy contracts and supported envelopes come from the six completed earlier labs.
The Lua guard and byte-client adapter are supplied; you do not need to learn Lua to implement
the three Python operations. This package never imports learner code into the academy API.

## Install and run

Use Python 3.13+. Complete and build the earlier service, competition, outbox, worker, stream
and migration labs first. Install their six 0.1.0 wheels with this package in a fresh virtual
environment. Local artifact paths must match files you actually built:

```sh
python -m pip install /path/to/completed/wheels/*.whl
python -m pip install -e '.[dev]'
python -m pytest -q
python -m mypy --strict src demo.py
python -m build
```

The academy repository's maintainer command `make verify-delivery-recovery` builds all seven
completed source archives/wheels and runs copied tests outside source. It uses maintained
references, which are excluded from your starter. For your own evidence, install **your**
wheel and copy these tests/demo outside your source tree; run them there with `python -I`.

Live tests and demo require `ACADEMY_RECOVERY_DSN` and `ACADEMY_BROKER_URL` pointing to
explicitly disposable PostgreSQL 17 and Redis 7.4 stores. Keep credentials in private
environment configuration. Fixtures own only generated schemas and namespace stream keys.
No FLUSHDB, production database or shared key deletion. Without both stores live cases skip;
those skips do not evaluate recovery. Run `python -I demo.py --output recovery.json` outside
source to save actual evidence. Passing public cases is finite evidence, not certification.

## Three precise contracts

1. **inspect_dead(engine, namespace, limit=8)** validates an exact namespace and exact integer
   limit 1–64 before connection. It returns copied DeadJob values in id/revision order for
   current, unacknowledged dead jobs in that namespace only. It does not mutate state.
2. **redrive(engine, job, approve=True)** revalidates the exact copied snapshot before
   connection. Exact explicit approval is required. One UPDATE matches complete Event
   identity/value, reason, generation, saved maximum and current dead state. Only poison jobs
   with remaining attempts can become ready now. Preserve generation and policy; set reason
   retry. Repeat/concurrent/stale/missing/conflicting requests return False. Exhaustion stays
   terminal; it needs a separate recovery design. The next claim increments generation;
   old leases cannot settle. True means a local committed state change, not remote delivery.
3. **prune(engine, broker, namespace, id, allow_loss=True)** accepts the supplied RedisBroker
   and one exact stream ID. Read one supported same-scope envelope; require matching local
   inbox/outbox values, producer acknowledgment and done job under shared row locks. The
   supplied Lua checks the unchanged payload, 1–8 current groups, each group's delivered
   position and no pending reference to that ID, then XDEL in one atomic Redis execution.
   Return removed/missing/blocked. Unsupported envelopes raise before effects. **Never delete
   PostgreSQL facts, outbox, inbox, effects, policy or jobs.** All keys and generations survive.

Operations borrow the Engine/client; own and release each PostgreSQL transaction. Use the
previous owned_session with one attempt, 250ms lock and 5000ms statement limits. No automatic
retries. A database exception rolls back database state, but cannot undo a Redis deletion.
The live failure case demonstrates this. After uncertain deletion, inspect the exact ID;
missing is not proof of a consumer effect. Existing deduplication records keep replay safe.

## Retention runbook and limits

Diagnose poison before approving redrive; do not mutate an Event to hide the original failure.
Freeze consumer-group creation/destruction and SETID rewinds while choosing/removing payloads.
The script protects **current** groups only. A new/rewound group cannot recover removed payloads;
this is explicit replay-history loss. No bulk trim, TTL, automatic age horizon or poisoned
broker-message redrive is implemented. IDs are caller selected, not inferred from wall time.
The previous schema has no completion timestamp, so an age policy would invent information.

Group metadata is retrieved before the eight-group guard; trust a bounded configured topology.
Lua blocks other Redis commands during its execution; there is no hard callback deadline or
cross-store transaction. Native errors can include private details and stay in local diagnostics.
Deletion is not independently confirmed AOF/replication persistence. Retained PostgreSQL rows
can grow; deleting/archiving their deduplication keys requires a proven replay horizon and a
separate migration/recovery plan. No production backup/failover or arbitrary external effect
guarantee is claimed.

## Evidence for review

Save command/output, actual JSON, installed versions and cleanup. Add two regressions. Explain
the poison→ready→generation-2 trace, exhausted refusal, stale settlement and concurrent result.
Show pending/unread group refusal and exact payload deletion while every local history row is
unchanged. Replay the same Event at a new transport ID and observe one local application.
Review inspection/redrive, retention/replay, failure boundaries and installed observations
against the four manual criteria. Report skipped checks honestly.

Primary readings: [XDEL](https://redis.io/docs/latest/commands/xdel/),
[group metadata](https://redis.io/docs/latest/commands/xinfo-groups/),
[pending entries](https://redis.io/docs/latest/commands/xpending/),
[atomic scripting](https://redis.io/docs/latest/develop/programmability/eval-intro/).
