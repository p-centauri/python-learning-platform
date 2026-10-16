# ADR 0029: Versioned events and AOF stream delivery

Date: 2026-10-04. Status: accepted for this bounded local teaching unit.

## Context

ADR 0028 commits finite leases and fences producer settlement, but its publisher directly invokes a local database sink. The next authorized unit requires an actual broker acceptance boundary, supported event shapes, pending recovery and duplicate-safe local application. PostgreSQL producer, Redis and PostgreSQL consumer do not share one distributed commit.

## Decision

Publish six ordered lessons with separate Stream delivery contracts and complete original scenario/guided/diagram/glossary/private recall layers. Deliver a fixed authenticated fifteen-file extension with three unfinished functions and four manual criteria. Preserve earlier packages/Event/Accepted/HTTP routes/permissions/denominators and frozen histories. The academy serves bytes/stores reported evidence only; no learner execution or runtime/React/schema/runner change. redis-py 6.4.0 is added only to maintainer development dependencies and this local package.

Define exact v1 flat and v2 key/data reading envelopes mapping to the same Event key. Use deterministic compact bytes, a 1024-byte parser bound, UTF-8, duplicate/non-finite rejection and exact shape/type/range/authorized-scope validation. Reject unknown kinds/versions before effect or success acknowledgment, keeping pending work for inspection. This is explicit compatibility for two versions, not arbitrary forward compatibility or an automatic migration.

Use Redis Streams on digest-pinned Redis 7.4.2 with AOF/appendfsync always/noeviction. The supplied adapter leases a dedicated physical connection from the borrowed configured byte client for XADD then WAITAOF 1 0 1000; check stream ID/local flush count before Accepted and release the connection. Producer completion implies this broker boundary only, not a consumer effect. Unconfirmed appends may exist; retries preserve Event identity and can create different transport IDs.

Explicit group setup at 0-0 includes existing entries and preserves an existing group's position. Request at most one new or recovered entry. Validate, commit the previous transactional inbox/local aggregate, then XACK. Expose recovery continuation/deleted IDs, rather than claiming global emptiness or inventing missing payloads. No trimming, dead-letter/redrive, consumer retry loop or owner-fencing claim. XACK removes pending state, not retained payloads.

## Evidence

74 public cases: 59 offline and 15 actual PostgreSQL/Redis-dependent cases. Fresh installed five-package evidence passes all on PostgreSQL 17.11, Redis 7.4.2 and redis-py 6.4.0. Source/archive/wheel construction, pip consistency, resources/quiet import, strict installed demo/process types, actual JSON/readback and prior API 401/403/200/output pass. Real checks separate producer completion from consumer effect, both versions/zero, duplicate/conflicting facts, unknown/wrong-scope payloads, pending/new distinctions, idle reclaim, deleted gaps, actual CHECK rollback and retained entry after acknowledgment.

Real child exits 91 after broker flush before producer settlement and 92 after consumer commit before XACK preserve the named repeat windows. Parent observes tagged database/broker connections vanish and actual lease/idle eligibility before replay. Generation-2 publication creates two transport entries and one application; pending reclaim confirms one existing effect. A controlled broker restart retains an entry and pending group state on the same AOF volume.

An initial restart test correctly failed because Docker reassigned a dynamically published host port even though the broker restarted successfully. Sanitized owned diagnostics confirmed healthy AOF reload. The helper now selects/publishes a loopback port explicitly to preserve it across restart; final verification passes. Fixture finally blocks release database ownership even if broker cleanup fails. Owned container/network/volume/private configuration are removed after checks. Remote CI is configured but unobserved.

## Consequences and limits

Broker acceptance, local effect commit and pending acknowledgment remain separate. The inbox protects only a local database effect, not email/payment/external exactly-once semantics. Pending idle/ownership and producer fencing do not terminate old consumers; XACK lacks an owner-token check. A parser guard follows retrieval, so COUNT/1024 bytes do not establish hostile-wire memory isolation or hard total deadlines. Scope fields are not credentials; public ACL/TLS, global fairness, retention/redrive and full operations remain separate.

Controlled restart while PostgreSQL stays alive is not power-loss/failover/volume-loss/backup recovery. The AOF test volume is owned and removed afterward. Prior additive teaching SQL remains outside combined production migration/drift integration. Finite tests and manual evidence never certify expertise or award mastery.

Step 6 remains open. Next rehearse versioned combined delivery-schema migrations with existing service_002 facts and installed head/drift/rollback evidence. Then retention/redrive, release/deployment, deeper SQL/API and applied AI remain.

Primary reading: [Redis WAITAOF](https://redis.io/docs/latest/commands/waitaof/), [XREADGROUP](https://redis.io/docs/latest/commands/xreadgroup/), [XAUTOCLAIM](https://redis.io/docs/latest/commands/xautoclaim/), [XACK](https://redis.io/docs/latest/commands/xack/), [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/), [redis-py 6.4.0 release](https://github.com/redis/redis-py/releases/tag/v6.4.0).
