# ADR 0045: Proxy trust boundary and per-account sign-in limit

Date: 2026-10-26

Status: Accepted

## Context

On the shared server every request reaches the API through Caddy and then the Next.js web tier. uvicorn ran without proxy headers, so the per-address authentication throttle (20 login/registration/recovery requests per minute) keyed every visitor on the web container's address: all learners shared one bucket, and twenty failed attempts from anyone blocked sign-in for everyone for a minute. A per-address limit alone also cannot slow many addresses guessing one account's password.

Next.js 16.4 rewrites (`next/dist/server/lib/router-utils/proxy-request.js`, httpxy without `xfwd`) forward the incoming `X-Forwarded-For` unchanged and add none. Caddy, the only route to the web tier besides the host's loopback port, replaces any client-supplied value with the client address.

## Decision

The API image runs uvicorn with `--proxy-headers`. It honours `X-Forwarded-For` only from `FORWARDED_ALLOW_IPS`, uvicorn's default `127.0.0.1` elsewhere and the web container's fixed address on the server. In `docker-compose.server.yml` the web container sits on an internal `api_link` network with the API at `10.89.30.251` (Docker assigns only from `10.89.30.0/25`) and is not on the default network, so its requests always come from that address; the API trusts that exact address, never a network or `*`.

Login additionally counts failures per normalized email: five failures within fifteen minutes return 429 with `Retry-After` until the oldest expires. The check runs before password hashing and treats unknown emails identically, so it reveals nothing about which accounts exist. Successful sign-ins never count, and a locked account waits even with the right password. Like the existing per-address limit, the counters are per process and in memory.

## Consequences

Each learner now has an independent per-address limit, and a distributed guess against one account stops after five attempts. Tests cover the per-account lock, unknown emails, expiry, separate buckets behind the trusted web tier, and forwarded headers ignored from any other peer; the lock and untrusted-peer tests fail when the failure record or the exact trust is removed (checked).

Someone with shell access to the host can still send a forged header through the loopback diagnostic port. Counters reset when the API restarts, and a second API process would need shared storage (PostgreSQL or Redis); multi-instance throttling stays on the roadmap. An attacker can deliberately lock a known learner's account for fifteen minutes; that trade-off is standard for per-account limits and preferable to unlimited guessing.
