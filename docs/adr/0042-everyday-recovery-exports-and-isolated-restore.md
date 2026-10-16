# ADR 0042 — everyday recovery, evidence export and isolated restore

Date: 2026-10-12. Status: accepted for verified local academy use.

## Context

The final agreed learning-experience step needs the full academy to boot on PostgreSQL, retain work and recover access/data. Email delivery and public hosting are not configured. Existing SQLite learner history, private exam keys and separate manual evidence must survive. The initial real container boot exposed a content-path `IndexError` before settings could read `CONTENT_DIR`.

## Decision

Use root-safe content-path resolution and a five-service Compose order: PostgreSQL health → trusted database-role preparation → additive migrations/seed → API readiness → non-root standalone web. The application owns its schema through a restricted role, distinct from maintenance credentials; it has none of superuser/create-database/create-role/replication/bypass-RLS privileges. API/web receive no Docker socket. The Docker Desktop host bridge reaches the authenticated loopback controller on this verified installation; proxy environment settings cannot forward its token. Default execution remains disabled. A general server/public worker deployment is separate work.

Add only `account_recovery_keys` at migration `c3970b860e75`. A password-confirmed owner creates/rotates a random 256-bit offline key, shown once; only its SHA-256 digest is stored. It remains valid until use, revocation or password change. Recovery locks the owner, checks the digest, changes the password, consumes the key and revokes all sessions in one transaction. Failed well-formed requests do the expensive hash work and return one generic credential error. No recovery email, automatic login, security question or administrator reset endpoint is invented. Old accounts receive no key/backfill until their owner acts.

Mutation authentication rechecks the session **after** the owner-row lock: a queued request whose session was revoked while waiting must fail. Real PostgreSQL connections observed the lock wait and resulting 401; competing recovery calls return one 200 and one 401. Password/session controls share the owned mutation boundary. A per-process two-slot hashing semaphore and 256 KiB streamed mutation-body cap bound parts of local resource use; they do not provide shared ingress abuse protection.

Evidence exports are authenticated field allowlists, serialized through existing public exam/coding/recall/project views while locking owner/project records. They include private learner text/source and fixed public outcomes, excluding sessions/credentials/recovery keys/private definitions/active answer keys. Markdown fences keep personal text literal. Neither JSON nor Markdown is a database import format or a mastery/qualification award.

Trusted maintenance commands create new private backup files and require a matching digest/type manifest. SQLite uses its backup API with owned connections, integrity/FK checks and exact fingerprints. PostgreSQL custom dumps restore transactionally as the app role into a randomly named **new** database. Schema/head/content and, with stopped writers, complete row fingerprints are verified. Default checks remove the target; an explicit keep option retains only a successful new restore for operator recovery. Live overwrite is unavailable. Recovery traffic promotion requires explicit configuration, session/key revocation and business acceptance; it has not been performed on real learner data. Digests establish integrity, not archive authenticity. Restore SQL is trusted operator input, never an upload/API route.

Readiness checks the actual academy schema head/database; process liveness is separate. Desktop/mobile acceptance uses actual keyboard focus/escape/return behavior, 60 automated axe states and narrow-screen overflow checks. Visible muted text, mobile search labels, wrapping and the sign-in layout were corrected. The dashboard's decorative code mark uses the existing hidden SVG icon rather than prose. These checks are finite observations, not universal accessibility certification.

## Consequences and evidence

`docs/OPERATIONS.md` gives startup, separate database ownership, backup/check/retention and new-target recovery instructions. Original SQLite remains the primary local study history; the PostgreSQL verification deployment is separate and contains synthetic fixtures. Only the owned verification project is stopped/restarted; unrelated Docker resources remain untouched.

Step-eight evidence includes 232 backend checks, three backup safety cases, actual PostgreSQL recovery races, 25-table/338-record PostgreSQL and 25-table/4,790-record SQLite restores, clone migration rollback/re-upgrade, non-root runtime/restart/outage observations, 11 distinct browser journeys across runs, 60 clean accessibility states, production build/types/lint, a zero-finding npm audit and preservation of original 19-table learner state/all 670 content files/history prefix. Detailed commands/corrections/limits are in PROGRESS and `.local/everyday-20261012/`; remote CI is unobserved.

Email verification, multi-instance throttling, deploy-only migration ownership, offsite/PITR recovery, real traffic promotion/load/SLO/public TLS and public hostile-code execution remain open. The frontend audit now runs in CI; Next 16.4.0 and compatible transitive patches resolve the observed dependency advisories. The broader expert curriculum, real-model/production evidence and independent learner artifact judgment remain separate acceptance requirements.
