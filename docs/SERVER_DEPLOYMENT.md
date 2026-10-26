# Academy server deployment

Started 2026-10-16 at the user's request. Fresh accounts were explicitly selected; the existing local learning database is preserved and is not uploaded. Actual hosted acceptance is recorded below; all listed deployment checks are complete.

- [x] Inspect existing server and preserve the carwash application boundary.
- [x] Verify temporary hostname DNS, generate unique private credentials and validate isolated Compose settings.
- [x] Upload source without local databases, credentials, node_modules or development caches; verify the release archive/digests.
- [x] Check current API/frontend advisories (zero known findings), Python lint and TypeScript.
- [x] Validate the academy Caddy addition and save the original proxy configuration/container baseline privately.
- [x] Complete actual Docker build, restricted-role migrations/seed, non-root serving, health/resource/restart checks.
- [x] Enable only the academy HTTPS route through a graceful proxy reload; verify the original carwash containers/routes remain healthy and unrestarted.
- [x] Verify actual browser account/learning/assessment/recovery/export flows, Secure cookies, origin enforcement, active answer privacy and unavailable runner behavior.
- [x] Verify private backup/isolated restore and persisted data/restart, remove only deployment test fixtures, document rollback/operations and close out durable status/history.

## Addresses and ownership

Server `aiagent@45.141.22.101`; identity `~/.ssh/contabo_aiagent`. Host directory **`/srv/aiagent/academy`**, Compose project **`engineering-academy`**, persistent PostgreSQL volume **`engineering-academy_academy_data`**. Credentials are generated on the server in mode-0600 **`.env.server`** and are not printed/copied into documentation. Keep `.local/` evidence and snapshots private.

Temporary HTTPS origin: **`https://academy.45-141-22-101.sslip.io`**. The service [sslip.io/nip.io](https://nip.io/) resolves IP-containing hostnames to the embedded address and supports ordinary per-host certificates. It avoids buying a domain for this deployment, but depends on third-party DNS availability. An owned domain can replace it later.

Carwash remains in `/opt/apps/carwash`, project `carwash`, with its existing volumes. Its Caddy proxy already owns 80/443. Only academy **web** joins the existing `carwash_default` network with the unique alias `engineering-academy-web`; academy API/database remain on the academy network. The web diagnostic port binds **127.0.0.1:3100**, not the public interface. No new host firewall rule is needed.

## Server commands

Run from `/srv/aiagent/academy`, using both files and the exact project. Do not use generic commands from the carwash directory.

```sh
docker compose --env-file .env.server -p engineering-academy \
  -f docker-compose.yml -f docker-compose.server.yml config --quiet
docker compose --env-file .env.server -p engineering-academy \
  -f docker-compose.yml -f docker-compose.server.yml up -d --build
docker compose --env-file .env.server -p engineering-academy \
  -f docker-compose.yml -f docker-compose.server.yml ps -a
```

The server override adds `unless-stopped`, bounded logs, memory/CPU/PID limits, non-root serving with dropped capabilities/no-new-privileges, web health and Secure cookies/exact HTTPS Origin. Application and maintenance database roles/credentials are separate. `migrate` upgrades/seeds before serving; no shared/demo account is seeded. Create your account in the UI.

## Execution boundary

This first shared-server deployment deliberately has **no Docker coding controller configured**. Lessons, account/progress, objective knowledge exams, saved code drafts/history and project/review work use the academy API/database. New coding/SQL runs and practical-repair execution require a verified separate worker; controls report unavailable while preserving drafts. Offline learner starter packs remain downloadable.

The existing controller has powerful Docker authority and was verified for local personal use. Mounting the shared server Docker socket into API/web or a public runner would risk the carwash application. No socket or worker port is added here. A separately isolated Linux worker is a later deployment task, with its own permission/resource/cleanup acceptance. This deployment does not complete the broader public multi-tenant hardening roadmap.

## Proxy update and rollback

> **2026-10-26: superseded.** The server now has one shared proxy, `/opt/apps/proxy` (see its
> README for sites, commands, adding an app and rollback), owned by no app; carwash's own Caddy,
> `Caddyfile.ip` and the reload procedures below are retired. The academy is served at
> **https://eng.xosilov.com**; its web container joins the `eng-edge` network (alias
> `engineering-academy-web`) and an internal `api_link` network at `10.89.30.251` (ADR 0045), and
> `.env.server` has `ACADEMY_ORIGIN`/`ALLOWED_ORIGINS=https://eng.xosilov.com` and
> `ACADEMY_PROXY_NETWORK=eng-edge` (previous file: server `.local/proxy-move-*/`). The sslip.io
> address permanently redirects there. Edit `/opt/apps/proxy/Caddyfile` in place, validate and
> reload as its README says. The text below describes the earlier setup.

The existing Caddyfile is `/opt/apps/carwash/deploy/caddy/Caddyfile.ip`. The original is backed up privately at `/srv/aiagent/academy/.local/deploy-20261016/Caddyfile.before`; container IDs/start times/restart counts are saved alongside. Candidate configuration appends only the academy site and explicit hostname HTTP→HTTPS redirect; validation occurs inside the running Caddy container before activation.

Caddy uses a read-only single-file bind mount. Preserve the host inode when writing the validated candidate, and compare host and mounted bytes before relying on `/etc/caddy/Caddyfile`. A previous atomic file replacement can leave the running container bound to an older inode even when the source path is correct. This was observed on 2026-10-19. An in-place host write alone does not repair that existing stale binding.

For a graceful reload that works with a stale binding, copy the reconciled candidate into the container, validate those exact bytes, then reload from that candidate. Keep the same complete configuration on the host for future starts. Example, after backing up the current file and checking for concurrent edits:

```sh
docker cp /opt/apps/carwash/deploy/caddy/Caddyfile.ip \
  carwash-reverse-proxy-1:/tmp/shared-proxy-reviewed.Caddyfile
docker exec carwash-reverse-proxy-1 caddy validate \
  --config /tmp/shared-proxy-reviewed.Caddyfile --adapter caddyfile
docker exec carwash-reverse-proxy-1 caddy reload \
  --config /tmp/shared-proxy-reviewed.Caddyfile --adapter caddyfile
```

Use a new candidate filename per operation, compare its bytes/hash with the intended host configuration and stop on a concurrent edit. Do not reload a stale mounted `/etc/caddy/Caddyfile`; it would remove the academy again. Reload is graceful and must not recreate/restart Carwash containers. If activation or Carwash continuity fails, restore the exact backed-up host bytes **in place**, copy that rollback configuration into the container, validate and gracefully reload it. Do not overwrite later edits blindly.

Every future shared-proxy/Carwash deployment must retain both academy site blocks from `deploy/Caddyfile.academy` in its complete candidate. Before considering that release complete, verify trusted HTTPS academy `/login`, `/api/health` and Carwash `/health`; a healthy private academy container cannot prove its public route exists. This is an operator release requirement, not an automated route-preservation mechanism.

To disable only the academy, remove its added site block from the current configuration after checking for later edits, validate and gracefully reload. Stop only the `engineering-academy` project with the same two Compose files. Preserve its database volume; never use `down -v` as a restart. Rolling back application code requires a compatible schema and the retained private database backup, not an automatic destructive downgrade.

## Verified deployment (2026-10-16)

- Full server Docker build/standalone Next 16.4.0, migrations/seed and head `c3970b860e75` pass. The database starts with zero accounts and 195 lessons; all five privileged-role flags are false. API/web run as UIDs 10001/1000. Serving/database resource/restart limits and private diagnostic/network/socket boundaries are observed.
- Trusted HTTPS `/login`, `/api/health` and liveness return 200. HTTP redirects to the correct academy hostname. Actual registration uses Secure/HttpOnly/SameSite cookies; wrong Origins/missing mutation headers return 403 and unauthenticated export returns 401. Personal notes save/export and active exams exclude private definitions. Caddy enforces a 512 KB ingress limit (API keeps its tighter 256 KiB cap); security headers are deferred so upstream values are overwritten once.
- Hosted Chrome: eight unique journeys verified across runs. Initial eight-test run: seven pass, one strict locator ambiguity between independent loading/note status regions. Scoped the assertion to the actual note-save message; the affected complete learning journey passes on rerun (14.0s total). No product runtime change was needed. Three Python levels, diagnostic, recovery/export, keyboard and **60 clean axe states** pass. The real [390px hosted view](screenshots/server-academy-mobile.png) was inspected.
- Saved note, code draft, active exam and the same authenticated session survive an academy database/API/web restart. Execution returns expected 503, preserves the separately saved draft and creates no grade. Carwash remains 200; its IDs/start times/restart counters are unchanged.
- Ten specifically identified synthetic deployment accounts were removed with FK cascades; no real accounts were targeted. Fresh database then has zero accounts. The earlier fixture snapshot was superseded by **`.local/backups/academy-20261016-clean.dump`** plus its manifest: actual isolated restore **25 tables / 263 records**, head/content/constraints verified; target removed, live state unchanged. This is an online snapshot, not a claimed stopped-source comparison.
- `npm audit --json` and `pip-audit -r apps/api/requirements.txt --format json`: zero known findings. Python lint/TypeScript and three backup safety tests pass. The PostgreSQL CLI now runs with server-standard Python; SQLite-specific imports are deferred. Local database bytes, all 670 content hashes and prior progress remain intact. No local learning history was uploaded or local runtime restarted.

Private server evidence is `.local/deploy-20261016/`; local deployment evidence is `.local/deploy-20261016/`. Original source archive SHA-256: `508e7e7f920f22190eff58edd5a1c900964e34d6e67fc487dbb5856d81e43a06`. Explicit overlay digests record the final Caddy template, maintenance CLI, corrected source test and operating documents. No credential values belong in a release manifest.

## Back up and stop this installation

From `/srv/aiagent/academy` (choose a new archive name each time):

```sh
python3 scripts/academy_backup.py postgres-backup \
  --project engineering-academy --env-file .env.server \
  --output .local/backups/academy-NEW-DATE.dump
python3 scripts/academy_backup.py postgres-restore-check \
  --project engineering-academy --env-file .env.server \
  --archive .local/backups/academy-NEW-DATE.dump
```

Keep archive/manifest mode 0600, trusted and encrypted offsite. The current retained clean baseline contains no real learner accounts; take a fresh backup after actual learning starts. Actual promotion, old-session/key revocation and restore scope are in OPERATIONS. Stopping the local Mac/Docker does not stop this server installation.

```sh
docker compose --env-file .env.server -p engineering-academy \
  -f docker-compose.yml -f docker-compose.server.yml stop
```

This stops only the academy and preserves its volume. Restart with the corresponding `up -d` command above. Future carwash/proxy deployments must retain the appended academy site block; blindly replacing the shared Caddyfile would remove its route. Do not reboot the shared host or stop/prune unrelated projects as an academy restart.

## Remaining operating scope

Account recovery requires the offline key generated while signed in; no email delivery is configured. Email identities/reviewer qualifications remain unverified. API auth throttling is per-process with one API instance; ingress body limits/resource caps help this deployment but do not establish scale/abuse/SLO acceptance. Database backups remain sensitive and need independent encrypted retention/offsite copy. Neither production-host reboot, disaster traffic promotion, realistic load nor a public hostile-code worker is certified by these checks.

## UI/UX frontend update (2026-10-16)

A later user-authorized frontend redesign is now deployed; see UI_UX_REVIEW and ADR 0044. It changes fifteen frontend source files, including a self-hosted licensed font and shared responsive styles. The API, schema, curriculum, learner-data contracts and proxy configuration are unchanged. Web image is `sha256:ea5cc4ec3011b00ff4495715fa96441fe2c233c65399dfd5e1ffcfca07156178`; only web was recreated, with all other ten container identities/start times/restart counters verified unchanged.

For an already reviewed frontend-only update, build then activate web without its dependencies:

```sh
docker compose --env-file .env.server -p engineering-academy \
  -f docker-compose.yml -f docker-compose.server.yml build web
docker compose --env-file .env.server -p engineering-academy \
  -f docker-compose.yml -f docker-compose.server.yml up -d --no-deps web
```

Before activating, save the current image/source and verify no concurrent source change. This release retains `engineering-academy-web:before-ui-ux-20261016` plus server-private `.local/ui-ux-20261016/before-source/` and manifests. A runtime rollback can retag that retained image to `engineering-academy-web:latest` and run the same `up -d --no-deps web`; source rollback must separately reconcile the recorded files before a later rebuild. Never restore old source blindly over subsequent work. No database downgrade is needed for this presentation-only change.

Live verification for this update is read-only: public login/recovery/assets/health/security headers pass, with no API mutation and no production test account. Automatic approval review rejected the proposed production-data fixture; authenticated learning/filter/note/assessment UI was instead checked in an isolated local standalone production build. The earlier deployment's authenticated checks remain historical evidence, distinct from this update's test scope. Root RELEASE.json retains the previous manifest and the new source/image record. Local previews were stopped; the hosted installation remains healthy.

## HTTPS route recovery (2026-10-19)

The user's outage report reproduced as a TLS internal-error alert for the academy hostname. All three academy services were healthy and private login returned 200; Carwash HTTPS was also healthy. Both academy site blocks were absent from the current shared host/mounted configuration. The specific edit that removed them was not established.

Saved current proxy bytes and nine container identities/start times/restarts under server-private `.local/outage-20261019/`. Appended the academy template to the current configuration, preserving every Carwash byte as the prefix. Candidate validation passed. The first guarded activation detected a stale read-only bind after writing the host file and stopped before reload. Activated the independently verified container candidate `/tmp/academy-outage-20261019.Caddyfile` instead, without recreating a container. The current host configuration SHA256 is **2cf3d4089c727729859b39fccee11914f598f031bfdd911e3fa6d3836e813fed**; the incident's previous Carwash-only prefix SHA256 is **5c80ffa72a0a5a8058d60d30941171e96445dfd76a71943290d0b28b6eb80e7c**.

Trusted public login/recovery/readiness/liveness return 200, browser rendering and sign-in mode work, and four security headers remain single-valued. An initial `/api/health/ready` diagnostic probe returned 404 because readiness is `/api/health`; the corrected check passes. Carwash health remains 200. All nine running container IDs/start times/restart counts match the baseline. No application source/image/schema/learner record was changed, no database restore or app restart was performed, and no production test account was created. Screenshot: [restored sign-in](screenshots/academy-restored-20261019.jpg). The current container's mounted file remains stale; use the verified-candidate reload method above for subsequent changes until its bind is refreshed during a separately planned proxy recreation.
