# ADR 0043 — academy site beside the existing carwash deployment

Date: 2026-10-16. Status: accepted for this first hosted academy deployment.

## Context

The user authorized deploying the academy to their inspected server, selected fresh accounts and has no owned domain yet. CarWash Control already uses its own Docker project, persistent data and Caddy on ports 80/443. The local academy database must remain preserved, and a powerful local coding controller must not gain authority over the shared server through the academy API.

## Decision

Deploy to `/srv/aiagent/academy` with project `engineering-academy`, a distinct PostgreSQL volume/credentials and the existing additive migrations/seed. Upload source only: exclude local databases, secrets, caches and installed dependencies. Retain an archive/digest manifest and explicit deployment overlay digests. Generate server credentials on the server, mode 0600. No account/admin password is seeded; register in the UI.

Use temporary hostname `academy.45-141-22-101.sslip.io`, verified to resolve to the server. Caddy obtains an ordinary trusted certificate; later an owned domain can replace this third-party DNS dependency. Preserve the carwash Caddyfile bytes and privately snapshot container identities/start times before adding an academy-only site. Validate inside the installed Caddy, write the single-file bind mount in place and gracefully reload. Roll back the original bytes if reload or existing-app continuity fails. Do not recreate the existing proxy or change its routes, volumes or firewall.

Only academy web joins the existing `carwash_default` proxy network, with unique alias `engineering-academy-web`. API/database remain on the academy network. Diagnostic web access is loopback-only at 3100. No new public port or Docker socket is exposed by the academy. Server overrides add restart policies, bounded logs, memory/CPU/PID caps, non-root web/API with dropped capabilities/no-new-privileges, exact HTTPS Origin and Secure cookies. Initial operation uses one API instance; shared throttling is still future hardening.

Keep coding/SQL/practical-repair execution unavailable on this shared deployment. The current controller's Docker authority and finite local isolation verification are not public multi-tenant acceptance. A separate isolated worker needs its own Linux/profile/admission/cleanup verification. Existing saved draft/history, local starter downloads and all non-execution learning/review work remain available; unavailable execution must create no grade and lose no draft. Never mount the shared host Docker socket into API/web to bypass that boundary.

PostgreSQL maintenance uses host Python's standard library for Docker orchestration; defer SQLite-specific Python imports until SQLite commands are called. This avoids modifying server Python packages for backup operations. Restore only into new isolated databases. Online snapshots can legitimately differ from later live records, so no false stopped-source comparison is claimed.

## Acceptance and remaining scope

Require real build/migration/seed/private-role/non-root/resource checks, trusted HTTPS/redirect/auth/origin/cookie/privacy verification, hosted browser journeys, actual backup/restore and persisted fixture data across an academy-only restart. Preserve carwash container IDs/start times/restart counters and health; remove only synthetic deployment fixtures. Record exact results in SERVER_DEPLOYMENT/STATUS/PROGRESS before marking this deployment complete.

This publishes the working academy core; it does not complete public hostile execution, email identity/reviewer qualification, shared abuse controls, load/SLO/offsite/PITR/disaster promotion or every original graduate criterion. Local services remain intentionally stopped, with local learner history unchanged. User-requested future curriculum work remains a separate milestone.
