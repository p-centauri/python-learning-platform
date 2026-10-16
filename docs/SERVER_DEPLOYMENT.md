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

The existing Caddyfile is `/opt/apps/carwash/deploy/caddy/Caddyfile.ip`. The original is backed up privately at `/srv/aiagent/academy/.local/deploy-20261016/Caddyfile.before`; container IDs/start times/restart counts are saved alongside. Candidate configuration appends only the academy site and explicit hostname HTTP→HTTPS redirect; validation occurs inside the running Caddy container before activation.

Caddy uses a single-file bind mount. Preserve that inode when writing the validated candidate, then use `docker exec carwash-reverse-proxy-1 caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile`. Reload is graceful and must not recreate/restart carwash containers. If activation fails, restore the exact backed-up bytes **in place** and reload, leaving the academy private for diagnosis. If someone else changes the proxy file after inspection, stop and reconcile that change rather than overwriting it.

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
