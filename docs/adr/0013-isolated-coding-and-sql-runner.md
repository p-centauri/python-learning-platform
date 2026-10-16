# ADR 0013 — isolated coding and SQL execution

Date: 2026-09-30. Status: accepted for local personal use.

## Decision and scope
Learning-experience step 3 adds six authored exercises (three Python function contracts and three PostgreSQL queries), 25 finite checks, a keyboard-accessible text editor, saved drafts and fixed run history. Definitions live in `content/coding-exercises.json`, version `2026.09-code-v1`; private cases never enter React or learner responses. This is practice evidence, separate from scenario mastery, knowledge exams and manually reviewed project artifacts. Passing cannot establish complete correctness, quality or expertise.

The API only validates, persists and sends source over authenticated HTTP to a separate loopback runner. It never imports, interprets or executes submitted source, and has no Docker socket. The trusted runner controls Docker using fixed argument arrays; Python source executes only inside a fresh container per case. The outer trusted service compares returned values/errors and unchanged inputs. Learners cannot choose images, driver, commands, resources, fixture setup or expected answers. A protocol forgery is still compared to the outer expected value. SQL executes as a non-superuser `learner` role with only database connection, schema usage and SELECT on authored fixture tables. The application database is never connected to a sandbox.

## Isolation profile `2026.09-runner-v1`

- Digest-pinned Python 3.13 slim Bookworm image: `python@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26`.
- Digest-pinned PostgreSQL 17 Alpine image: `postgres@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24` (17.11 in the verified image).
- Non-root UID 65532 (Python) or 70 (PostgreSQL), read-only root, all capabilities dropped, no-new-privileges, Docker default seccomp, no privileged mode, devices, bind mounts, Docker socket, host secrets or published ports; network mode `none`.
- 0.5 CPU, 32 processes, 256 file descriptors, no core dumps. Python: 128 MiB memory with no additional swap and 8 MiB noexec/nosuid/nodev scratch tmpfs. SQL: 256 MiB memory with no additional swap, 192 MiB ephemeral database tmpfs, 8 MiB scratch and 1 MiB socket tmpfs.
- Python execution / SQL CLI bound to 4 seconds; PostgreSQL statement timeout 1.5 seconds, lock timeout 0.5 seconds and idle transaction timeout 1 second. Container preparation and execution share a 45-second job budget; cleanup has its own 5-second bound. Docker pipes have a combined 16 KiB output cap and are read incrementally. Timeout/output floods stop remaining checks and return finite failure evidence.
- Exact container inspection occurs before execution. Containers are forcibly removed on success/error/timeout/output flood. Startup only removes expired containers with the exact runner profile label; it never prunes unrelated Docker resources. Cleanup/environment failure disables execution until restart and verification.

SQL is submitted through a COPY query using fixed psql arguments and no shell. Learner text is never interpolated into a host shell command. The PostgreSQL socket must use `/var/run/postgresql`: the official entrypoint's temporary initialization server uses that path too. Readiness also checks that PID 1 has become `postgres`, preventing probes against the temporary bootstrap server.

## Admission, persistence and secrecy
A mode-0600 ignored `.local/runner.env` holds a generated service token, at least 32 characters. Runner endpoints require a constant-time token comparison and bind to loopback port 9000. The API shares that token but browsers and sandboxes never receive it. One job runs at a time, with busy requests rejected rather than queued. Authenticated API users get eight recorded runs per ten minutes across the lab, maximum 12,000 source characters and 16 KiB UTF-8; UUID request keys deduplicate successful retries. Existing PostgreSQL user-row locking serializes mutation admission; its concurrency remains unverified with the academy deployment DB. SQLite is only the local convenience database.

Migration `e953cd426a31` adds learner-owned coding drafts and immutable attempts with source, complete private definition snapshot, version, result and UTC timestamp. Offline drafts can be saved without execution. Unavailable/invalid responses create no grade. Both runner and API redact private case names/inputs/expected/actual/messages. Public cases show returned values and bounded diagnostics; all grades are validated against case count/status. Future content edits do not rewrite earlier attempts.

## Verification and limits
The worker remains unavailable until all 13 startup probes pass: non-root/seccomp/cgroups/no secrets, host/root filesystem denial, network denial, bounded/noexec tmpfs, process/memory limits, runaway termination, output cap, fresh filesystem, PostgreSQL fixture, restricted role, host-file denial and query timeout. `make verify-runner` repeats real Docker probes and tests all reference solutions and starters, input mutation, numeric type mismatch, forged status, aggregate deadlines, private feedback, HTTP authentication and admission. Browser checks use actual Python/PostgreSQL execution.

Docker containers share a kernel with the Docker VM/host; these verified controls are a local execution boundary, not proof against kernel exploits or a public hostile multi-tenant runner. The trusted runner's Docker-control authority remains powerful and must be isolated from public application infrastructure before a public release. Public scale requires stronger isolation review, admission/body/rate limits, durable queues/reservations, image vulnerability/update policy, telemetry, per-account abuse controls and restart/cleanup recovery. No third-party package installation, network-enabled exercises, arbitrary multi-file projects, asynchronous queue or AI grading is supported. Full Compose/PostgreSQL academy verification remains separate and unfinished.

## References
- [Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)
- [Docker seccomp profile](https://docs.docker.com/engine/security/seccomp/)
- [Docker network none](https://docs.docker.com/engine/network/drivers/none/)
- [PostgreSQL 17 GRANT](https://www.postgresql.org/docs/17/sql-grant.html)
- [PostgreSQL 17 COPY](https://www.postgresql.org/docs/17/sql-copy.html)
- [PostgreSQL 17 client timeouts](https://www.postgresql.org/docs/17/runtime-config-client.html)
