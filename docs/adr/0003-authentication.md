# ADR 0003 — opaque cookie sessions
Status: accepted. Date: 2026-09-14.

Use random bearer session tokens in HttpOnly, SameSite=Lax cookies; store only SHA-256 token digests in the database. Use scrypt for passwords with per-password random salts and constant-time comparisons. Require a custom request header and validate configured Origins for unsafe requests. Use Secure cookies in HTTPS deployments. This supports revocation without JWT lifecycle complexity.
