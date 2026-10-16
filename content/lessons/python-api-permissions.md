## The idea in plain language

Authentication asks which configured principal the caller represents. Authorization asks whether that principal may perform this operation on this resource. A known bearer token does not grant every namespace. Keep those questions separate even in a small local lab.

The factory snapshots one to eight caller-generated tokens, each bound to one namespace. There is no shared/default token. The authorization function accepts case-insensitive Bearer plus one space and a bounded ASCII token, compares credentials with hmac.compare_digest, validates the namespace and then checks exact scope. Missing/malformed/unknown credentials raise authentication failure; a known credential for another namespace raises permission denial.

In HTTP those become 401 with WWW-Authenticate: Bearer and 403 respectively. Permission is checked before the database session dependency. Filtering the SQL by namespace remains necessary after authorization: it stops another namespace's rows appearing in a query, including a caller-chosen pagination position. A cursor is a location, not a credential.

Never take the tenant from an unrestricted request body, trust a client-side disabled control or let a model decide access. Credentials and DSNs stay in private local configuration; responses and fixed logs do not expose them. An identifier's valid syntax says nothing about the caller's permission.

This credential map teaches a bounded local boundary. It is not public account management, OAuth, key rotation, recovery or multi-instance abuse protection. The academy already has separate real learner accounts; the package does not borrow their sessions. A future deployed service needs its own reviewed authentication/permission operations. The worked example illustrates scope only; the lab tests actual rejected requests before SQL and cross-namespace reads/writes.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
principal_scope = "feed"
requested_scope = "other"
print(principal_scope == requested_scope)
print("known identity still needs permission")
```

## Guided practice

Trace credential, principal scope, path and SQL filter. Explain 401 versus 403 without printing a token.

## Independent practice

Implement authorize and test malformed/unknown tokens, another namespace, extra body namespace and forged cursor positions.

## Check your work

Permissions run on every operation/page before database access; syntax and client UI are not authorization.

Continue to [Engines, sessions & request ownership](/lessons/python-sqlalchemy-sessions).
