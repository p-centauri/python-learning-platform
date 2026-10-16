# Existing server inspection

Inspected **2026-10-16** at the user's request, using their SSH connection. This was a read-only inspection; no academy deployment, source/configuration changes, service restarts, database writes, firewall changes or DNS changes were performed.

## Connection and capacity

- Host: `45.141.22.101`, hostname `vmi3667195`, SSH user `aiagent`.
- SSH identity supplied by the user: `~/.ssh/contabo_aiagent`. Known-host verification and non-interactive key authentication succeeded. Do not copy private key contents into this repository.
- Observed OS: Ubuntu 24.04.5 LTS, kernel 6.8.0-147-generic.
- **12 logical CPUs**, about **47 GiB RAM / 45 GiB available**; root filesystem about **387 GiB / 382 GiB available** at inspection. These are point-in-time readings, not a load/capacity benchmark.
- Public TCP listeners observed: **22, 80, 443**. DNS stub listeners are loopback-only. Docker is running; the supplied account belongs to its Docker group.

## Existing application

**CarWash Control**, at <https://45.141.22.101/>, is deployed from `/opt/apps/carwash` as Compose project **carwash**. Its private deployment environment file is `/opt/apps/carwash/.env.production`; secret values were not printed or copied.

| Container | Function | Observed state |
| --- | --- | --- |
| `carwash-reverse-proxy-1` | Caddy 2.11.7, public HTTP/HTTPS | Running; no Docker health check configured |
| `carwash-frontend-1` | Vue 3 / Vite / TypeScript frontend | Healthy |
| `carwash-backend-1` | FastAPI / SQLAlchemy / Alembic backend | Healthy; app user `appuser` |
| `carwash-postgres-1` | PostgreSQL 16 | Healthy |
| `carwash-redis-1` | Redis 7 | Healthy |
| `carwash-mosquitto-1` | Eclipse Mosquitto 2, MQTT | Healthy; nine recorded restarts |

All six have `unless-stopped` restart policies and JSON-file log rotation at 10 MiB × three files. Five containers have health checks and all five are healthy. All other inspected restart counters were zero. Recent broker stdout/stderr did not explain its historical restart count; no assertion of a diagnosed cause or full device/business health is made. An initial high PostgreSQL CPU sample returned to about 1.2% on the follow-up sample; it does not establish persistent load.

Caddy already owns public ports **80/443** and routes to the existing backend/frontend. The actual mounted configuration is `deploy/caddy/Caddyfile.ip`. Database/Redis/MQTT ports are container-internal in the inspected deployment; they are not published on host interfaces by Docker.

## Persistence and backups

Observed actual volumes:

- PostgreSQL: `carwash_postgres_data` at `/var/lib/postgresql/data`.
- Redis: `carwash_redis_data` at `/data`.
- MQTT: `carwash_mqtt_data` at `/mosquitto/data`, plus an anonymous log volume.
- Caddy: `carwash_caddy_config` and `carwash_caddy_data` for proxy state/certificates.
- MQTT configuration/ACL/password files are read-only mounts; their contents were not inspected.

`/opt/apps/carwash/backups` contains **three archive files**, about **285 KB total**, with latest observed modification **2026-10-16 03:15 Asia/Samarkand** (2026-10-15 22:15 UTC). File presence does not prove a successful/sufficient backup, offsite retention or recoverability. Archives were not opened or restored; no business records or credentials were read.

## Checks performed

- SSH `hostname`, `uname`, `uptime`, `id`; `free -h`, `df -h /`, CPU count and `ss -lntp`.
- `docker ps`, project listing, filtered container inspection, resource samples, persistent mounts, restart policies/counters and log rotation. No raw environment dump or raw application log output.
- Actual deployment composition validates with its `.env.production` and all three compose files (`docker-compose.yml`, `.prod.yml`, `.ip.yml`). The initial check without the required environment file failed; using the deployment's recorded environment file succeeds. No configuration was changed.
- Backend framework names checked from `pyproject.toml`; frontend frameworks from `package.json`. No project scripts/imports/builds/tests were executed on the server.
- From both server and user's computer, **HTTPS `/` returns 200** with title **CarWash Control**; **`/health` returns 200 JSON**, status `ok`. The IP-address TLS certificate verifies against default trusted roots and negotiates TLS 1.3; observed expiry 2026-10-22 07:05:14 UTC.
- `/api/health` and `/api/health/ready` return 404; this app's public health endpoint is `/health`, unlike the academy's `/api/health`. A localhost-IP probe does not match this IP-address TLS site; the actual public IP succeeds.

## Implication for the academy

The server has substantial currently unused resources, so coexistence appears feasible; this is an inference from inspection, not production acceptance. The academy is **not deployed here**. Its local services remain intentionally stopped with saved databases intact.

Any later authorized deployment must preserve the existing `carwash` project, private configuration and volumes; use a distinct academy project/database/volumes and an explicit routing plan for the already occupied HTTP/HTTPS ports. The academy's verified worker path is Docker Desktop-specific; Linux worker isolation/routing and the existing public-release gaps in SECURITY/ROADMAP need their own acceptance. Do not copy local learner history, expose the worker, replace Caddy or operate physical carwash devices as part of this inspection.
