# ADR 0031 — bounded retention and explicit redrive

Date: 2026-10-05
Status: Accepted

## Decision

Finish one four-lesson recovery unit with a separate twelve-file installable extension and
three unfinished Python operations. Keep the earlier delivery_004 schema and all six package
contracts. The API serves a fixed authenticated allowlist and stores manual evidence; it never
executes the package. A separate skill and v17 content layers preserve old denominators and
frozen exam/checkpoint/recall/project histories.

Inspection returns at most 64 copied current dead-job snapshots in complete-key order for one
authorized namespace. Explicit poison redrive uses one conditional PostgreSQL UPDATE matching
Event identity/value, generation, reason, saved maximum and current unacknowledged dead state.
It changes readiness only. Attempts and immutable policy remain; the next claim increments
generation and old settlement guards still apply. Exhausted jobs are refused. A replacement
budget or terminal-job reset needs a separate policy and schema design.

Retention removes one caller-selected Redis payload after matching local inbox/outbox values,
producer acknowledgment and a done job. Shared locks retain the local observations while a
supplied one-key Lua guard rechecks bytes and every current consumer group's delivered position
and pending reference before XDEL. Compare ID decimal components as strings, avoiding float
precision loss. Accept 1–8 current groups and no bulk traversal or trimming. PostgreSQL facts,
intents, inbox/effects, policy and jobs all remain unchanged.

Freeze group creation/destruction and cursor rewinds separately while selecting/removing
payloads. Future/new/rewound groups cannot replay removed history. The schema has no completion
timestamp, so inventing an age horizon would be misleading. Retained identity rows may grow;
deleting or archiving deduplication keys needs a proven replay boundary and separate recovery
work. Malformed broker-message repair and exhausted replacement are outside this unit.

## Evidence and limits

Seven source archives/wheels, fresh installation outside source, installed strict package/demo
types and packaged Lua/py.typed pass. All 36 public cases pass with no skips on actual disposable
PostgreSQL/Redis: 14 offline boundaries and 22 live cases. Actual concurrent redrive yields one
success; late database failure rolls back readiness; stale leases and exhausted jobs are refused.
Pending/unread groups block deletion; matching acknowledged groups permit it. Local history
survives pruning and a new transport ID carrying the same Event has one local application.

A live fixture really deletes the payload before raising inside the database transaction.
PostgreSQL rollback cannot undo that deletion. The demo records actual state, versions,
delivery_004 head, JSON readback and zero checked-out connections. Source tests may explicitly
skip stores; those skips provide no live recovery evidence. Learner reports/manual review do
not award mastery or certify expertise.

The script's atomic execution is limited to Redis. XINFO retrieves group metadata before the
eight-group guard; this assumes a trusted bounded topology. A borrowed database connection is
held during the synchronous broker command. SQL/client timeout settings do not establish a
hard whole-operation deadline. No deletion AOF/replication proof, shared cross-store transaction,
public ACL/TLS/hostile-client protection, arbitrary external exactly-once, production backup or
zero-downtime release is claimed. Current old service readiness is incompatible with the new
delivery head and is the next unit's concrete compatibility problem.

## Workflow consequence

Step 6 stays open. STEP_6_PATHS fixes nine remaining teaching/practical milestones with a clear
finish checklist. Each continuation finishes one bounded milestone; discoveries outside it
are recorded in the broader roadmap. Check new metadata/links and focused contracts first;
repeat broad checks only for shared changes or unresolved evidence. STATUS is a concise current
handoff; PROGRESS remains append-only and preserves detailed earlier evidence.

Primary references: [Redis atomic scripting](https://redis.io/docs/latest/develop/programmability/eval-intro/),
[group state](https://redis.io/docs/latest/commands/xinfo-groups/),
[pending range](https://redis.io/docs/latest/commands/xpending/),
[payload deletion](https://redis.io/docs/latest/commands/xdel/).
