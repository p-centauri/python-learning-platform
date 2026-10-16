# Running and recovering the academy

The host development academy uses `apps/api/academy.db`. Compose uses a separate PostgreSQL volume. Starting Compose does **not** import SQLite learning history. Keep those databases separate; the verification deployment on port 3100 contains synthetic test accounts only. The normal study address remains http://127.0.0.1:3000.

## Start PostgreSQL

Copy `.env.example` to an ignored private environment file and set unique maintenance and application passwords. Use URL-safe passwords (for example, generated with `secrets.token_urlsafe(32)`) because Compose builds the application connection URL from these values. Restrict the file to mode 0600. Maintenance and application usernames must differ. Use the exact browser Origin in `ALLOWED_ORIGINS`, matching `WEB_PORT`; HTTPS deployments need Secure cookies.

From the repository root, select the project you own. The default is `engineering-academy`; the current verification project is `academy-everyday-992c0f0c` with private `.local/everyday-20261012/compose.env` and port 3100.

```sh
docker compose --env-file .env -p engineering-academy up -d --build
docker compose --env-file .env -p engineering-academy ps -a
```

`db` waits until healthy. `db-setup` creates/restricts the application role and grants ownership of the academy schema. `migrate` upgrades and seeds once; `api` then becomes ready and `web` starts. The API/web run as non-root users. The app role is not a PostgreSQL superuser and cannot create databases/roles, replicate or bypass row security. It still owns the academy schema so migrations can run: a separate deploy-only schema owner is future hardening.

Only the web port is published, bound to loopback. `down` preserves the named database volume. **Do not run `down -v` to restart the academy.** Always use the owned project/env file; do not stop unrelated Docker projects. Changing `POSTGRES_PASSWORD` in an environment file does not rotate an existing PostgreSQL volume's password; coordinate an explicit role-password change privately.

The web API rewrite is captured at image build time through `API_INTERNAL_URL`. Runtime configuration alone cannot retarget an existing frontend image.

## Private execution on Docker Desktop

The trusted worker must already be configured and running with all 13 startup probes passing (`make runner-setup`, then `make dev` or the standalone `make runner`). There must be only one controller on port 9000 and no active execution during its startup probes.

```sh
.venv/bin/python scripts/configure_compose_runner.py
docker compose --env-file .env --env-file .local/compose-runner.env -p engineering-academy up -d
```

The helper writes a mode-0600 file without printing its token. On this verified Docker Desktop installation, `host.docker.internal:9000` reaches the authenticated host controller while it stays bound to host loopback. The API disables environment proxies for these private requests. Never put the token in browser code/logs, mount a Docker socket into API/web, or publish the controller port. This observed Desktop bridge does not establish a Linux/server worker topology. Default Compose has execution disabled until explicitly configured.

## Make private backups

Backups contain account identities, password/session/recovery hashes, private exam definitions and learner work. Keep archives **and** their JSON manifests outside Git, mode 0600, on encrypted storage with access controls. A digest catches changes; it is not a signature or proof of origin. Restore only archives you trust. Copy both files to an independently retained location and define a retention schedule; this project has not configured offsite storage.

Choose a new filename every time. These commands refuse existing destinations and never overwrite the serving database:

```sh
.venv/bin/python scripts/academy_backup.py sqlite-backup \
  --database apps/api/academy.db --output .local/backups/academy-20261012.db
.venv/bin/python scripts/academy_backup.py sqlite-restore-check \
  --archive .local/backups/academy-20261012.db

.venv/bin/python scripts/academy_backup.py postgres-backup \
  --project engineering-academy --env-file .env \
  --output .local/backups/academy-20261012.dump
.venv/bin/python scripts/academy_backup.py postgres-restore-check \
  --project engineering-academy --env-file .env \
  --archive .local/backups/academy-20261012.dump
```

SQLite uses the database backup API, then validates integrity/foreign keys and exact record fingerprints in a private copy. PostgreSQL uses `pg_dump`'s consistent custom-format snapshot, restores in one transaction as the restricted application role into a fresh random database, validates the restored schema constraints and compares migration/content provenance. It removes that database afterward, including on failure. Neither command serves traffic from the restored copy. Use the code/content revision recorded for the snapshot. Avoid migrations/content changes during a backup or restore drill.

For exact source-versus-restored record comparison, stop **only this project's** web/API writers before taking the PostgreSQL backup, keep them stopped during the check, and add `--compare-source`. Leave `db` running. A normal online backup is valid even when later source records differ.

```sh
docker compose --env-file .env -p engineering-academy stop web api
# Take a NEW PostgreSQL backup using the command above, then:
.venv/bin/python scripts/academy_backup.py postgres-restore-check \
  --project engineering-academy --env-file .env \
  --archive .local/backups/academy-20261012.dump --compare-source
docker compose --env-file .env -p engineering-academy up -d
```

## Recover into a new database

Do the restore drill first. PostgreSQL's `--keep-restored-database` option retains a **successfully verified new database** and prints its generated name. Failed restores still remove their target. It never replaces the original database:

```sh
.venv/bin/python scripts/academy_backup.py postgres-restore-check \
  --project engineering-academy --env-file .env \
  --archive .local/backups/academy-20261012.dump --keep-restored-database
```

For an actual recovery, stop serving writers; keep the original volume/snapshot. Privately copy the deployment configuration and set `POSTGRES_DB` to the exact generated restored name. Before routing traffic, connect a trusted maintenance client to **that restored database** and transactionally `DELETE FROM sessions; DELETE FROM account_recovery_keys;` so old backup credentials cannot regain access. This signs everyone out and requires each owner to generate a new offline key. Check schema/content, run the migrations appropriate to the chosen code revision, seed, and test sign-in, notes, exam/project evidence and worker access. Then explicitly start the owned deployment with the reviewed restored configuration. Retain the original database until recovery is accepted. Database creation/isolated restoration/cleanup is tested; traffic promotion, cross-host recovery and this incident procedure have not been performed on real learner data.

SQLite recovery also starts from a new file after stopping its own host processes. Validate a private copy first, revoke sessions/recovery keys in that copy, configure `DATABASE_URL` to its absolute path, migrate/check/seed and verify before serving it. Never replace an open SQLite file or copy only a WAL file. Keep the original available until recovery is accepted. The evidence export is for reading/portability, **not** a database restore/import format.

## Account access and evidence

At `/account`, confirm your current password, generate an offline recovery key and save its file securely. The key is shown only once and has no automatic expiry; rotation, revocation, use or a password change invalidates it. `/recover` needs that key plus your email. Successful recovery consumes it, changes the password and revokes all sessions without signing you in automatically. No recovery email is sent. Without a previously saved key, there is no automatic forgotten-password recovery.

The account page also changes passwords and revokes selected owned sessions. It shows expiration/current-session status, not invented device identities. JSON/Markdown downloads include your learning notes, drafts and fixed public results; credentials, sessions, raw private definitions and active answer keys are excluded. Exported personal text and source remain private, and reported/manual evidence does not certify mastery.

## Observe failures and verify releases

`/api/health` is database/schema readiness (current head `c3970b860e75`); it returns 503 when the database is unavailable or the schema is incompatible. `/api/health/live` only confirms that the API process responds. Readiness is not permission to execute learner code: the private worker has its own readiness probes. Update the expected head when adding future academy migrations. Do not solve a database outage by deleting its volume.

```sh
make test
make verify-backups
make lint
make build
cd apps/web
npm audit --audit-level=high
E2E_BASE_URL=http://127.0.0.1:3100 npx playwright test tests/everyday.spec.ts --workers=1
```

The everyday browser checks cover 60 explicit page states at 1280, 390 and 320 pixels plus real keyboard focus and recovery/download actions. Automated axe checks and observed Chrome journeys are finite acceptance evidence, not universal WCAG certification. The PostgreSQL competing-recovery/session drill is `python -m app.everyday_checks` inside the owned API container; it creates dedicated synthetic records. Run it only on an isolated verification database.

No point-in-time recovery/WAL shipping, offsite restore, load/capacity SLO, public TLS/proxy deployment, verified email identity, shared multi-instance throttle, or public hostile-code runner acceptance is claimed. Frontend dependency audit is automated in CI; remote CI has not been observed locally. Broader release acceptance remains in ROADMAP.
