# Redis Streams delivery lab

Complete the prior service, competition, outbox and leased-worker packages first. Build their local wheels; they are not downloaded from PyPI. Implement encode/decode in envelope.py and deliver in delivery.py. The shared Redis adapter, contracts and owned evidence helpers are supplied. The academy only serves authored files and stores reported evidence; it never executes your package.

## Exact event contract

Use the existing frozen Event(namespace,id,revision,value), its exact ASCII identity fields, revision 1..8 and value 0..1000000. Validate/copy again at each boundary; bool is not an integer value. The stable key remains namespace/id/revision, independent of envelope version, stream entry ID or delivery attempt.

encode supports exact integer version 1 or 2 (default 2), producing deterministic compact sorted-key bytes. Version 1 has exactly schema/namespace/id/revision/value. Version 2 has exactly schema/kind/key/data, kind reading, key containing exactly namespace/id/revision and data containing exactly value. This is an explicit compatible reader of two wire shapes, not an automatic migration or arbitrary forward compatibility.

decode accepts 1..1024 exact bytes, UTF-8 JSON and the authorized namespace. Reject duplicate fields at every nesting level, non-finite constants, unsupported version/kind, missing/extra fields, invalid types/ranges and a different namespace. Return a new validated Event. InvalidEnvelope contains a safe generic message. Never silently drop unknown versions or acknowledge them as success.

## Acceptance and consumption

RedisBroker borrows a configured synchronous redis-py client. Configure decode_responses=False, RESP2, finite connect/socket timeouts and Retry(NoBackoff(),0). The reference pins redis-py 6.4.0 and Redis 7.4.2. A client timeout is not a total callback deadline. Scope permission/TLS/public ACLs remain the caller's responsibility.

Explicit setup(namespace,group) creates academy:events:<namespace> with a consumer group starting at 0-0, so existing entries are included. BUSYGROUP preserves an existing group's position; other errors propagate. No import/request creates infrastructure. Tests use only generated owned namespaces, never FLUSHDB.

The supplied publisher adapts the leased worker to the broker. XADD and WAITAOF 1 0 1000 run on the same dedicated physical connection leased from the borrowed pool. Accepted is returned only after an exact stream ID and local AOF flush count of at least one; the owned connection lease is released afterward. Configure appendonly yes, appendfsync always and noeviction. A failed/missing confirmation can leave an appended entry: retry may add another stream ID for the same stable Event. Never return acceptance from just an in-memory XADD receipt or assume a failed reply proves no append.

That acceptance completes the producer job/outbox; it does not mean the consumer applied anything. PostgreSQL and Redis have separate commits. Preserve this boundary in reports.

deliver validates namespace/group/consumer, exact recovery bool, idle milliseconds 0..60000 and byte stream cursor. It requests at most one new entry using XREADGROUP with >, or uses XAUTOCLAIM for explicit pending recovery. Validate the payload, call the previous consume to commit inbox/local effect, then XACK that entry. Failure before acknowledgment retains pending work; original errors propagate. XACK 0 means this call removed no pending entry (it may already be acknowledged), not automatic missing-effect proof.

Return Result(event,entry_id,acknowledged,cursor,deleted). No returned message does not mean no pending work. Preserve and advance the supplied XAUTOCLAIM cursor across bounded recovery calls; restarting at 0-0 forever can starve later entries. Report deleted pending IDs honestly: a trimmed/deleted payload cannot be reconstructed. XACK removes the pending reference, not the retained stream entry. No automatic trimming, dead-letter/redrive, cursor loop or consumer-attempt policy is supplied.

The earlier inbox deduplicates both supported versions and multiple stream IDs by the same full Event key and rejects changed payloads. This protects one local database effect. Redis pending ownership/idle time does not terminate an old consumer, and XACK itself is not a fencing-token check.

## Run local checks

Build and install the five completed local wheels in a fresh environment, plus this package's dev extras. Copy tests, demo.py, worker_process.py and pyproject.toml outside source. Run pip check, pytest -q tests, mypy --strict demo.py worker_process.py, then python demo.py --output streams.json. Supply ACADEMY_STREAM_DSN and ACADEMY_BROKER_URL privately, only for explicitly disposable PostgreSQL/Redis. The suite has **74 cases: 59 offline and 15 live cases**. Missing either configured store explicitly skips live checks; skips are not broker evidence.

The trusted maintainer verifier owns a password-protected digest-pinned loopback Redis container, resource limits and a generated AOF volume, plus temporary PostgreSQL. Its ACADEMY_BROKER_CONTAINER identifies the owned container for the actual restart fixture; never point restart helpers at shared infrastructure. Public process evidence targets POSIX macOS/Linux. The parent observes actual child database and broker connections disappear after exit 91 (broker flush before producer settlement) and 92 (consumer commit before XACK). It observes database lease expiry or Redis pending idle time before reclaim. A controlled broker restart reads the same AOF volume and preserves entries/group pending state. This is not power-loss, failover, replication, volume-loss or backup recovery.

Save actual installed versions/JSON/readback, tests/types/artifacts and two regressions, then submit four manual criteria. Reported tests/checklists/reviews do not award mastery. No learner execution, external email/payment idempotency, exactly-once transport, hostile oversized wire protection, global fairness or full production operations claim. The 1024-byte parser guard follows broker retrieval; COUNT alone does not bound network payload bytes. Operational migration/retention/repair and release/deployment remain later work.
