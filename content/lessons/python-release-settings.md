Configuration tells a program where it may connect and which credentials belong to which namespace. Treat it as input with a clear owner. Read it once when creating a release, validate it, and make an independent copy. A caller editing its dictionary later should not silently change an already running service's permissions.

The local lab requires two private environment values: ACADEMY_RELEASE_DSN and ACADEMY_RELEASE_TOKENS. There is no built-in password or shared account. Tokens is a JSON object with one to eight distinct credentials, each mapped to a validated namespace. A credential is 16–64 ASCII letters, digits, underscores or hyphens; a namespace follows the earlier service contract. The DSN has a 1024-character bound and token JSON a 4096-byte bound. Reject duplicate JSON keys before they disappear into a dictionary.

Python's frozen dataclass is useful for ordinary callers, but it is not a security boundary against arbitrary Python code. The factory must validate and copy the settings again before allocating an engine. A malicious or mistaken caller can use object.__setattr__ to bypass normal assignment. Avoid trusting the type annotation or frozen flag as proof of current valid fields.

The example below uses a deliberately local label, not a usable credential. It illustrates a copy; it neither connects nor proves authentication. Changing the original mapping leaves the copied pair unchanged.

## Try a small example

```python
authority = {"local-token": "feed"}
snapshot = tuple(authority.items())
authority["local-token"] = "other"
print(snapshot[0][1])
```

Expected output: `feed`.

## Guided practice

Use the prediction before running the snippet. Explain which owner keeps the state, then use the debugging checkpoint to choose a change at the failure boundary. The diagram and glossary describe the same sequence in words.

## Independent practice

Implement load_settings using the supplied pure helpers. Test missing values, duplicate keys, too-short tokens, bad namespaces and oversized input. Confirm that importing the package and loading settings open no socket and perform no migration.

Do not print a DSN, Authorization header or token when a check fails. Settings hides sensitive fields in its repr; ConfigurationError has a generic message and suppressed cause. Private diagnosis can inspect the owner-controlled configuration separately. Keep local files mode 0600 and outside Git. This does not deliver a complete secret manager, automatic rotation or public identity service.

To rotate local authority, configure a new release and restart it deliberately. Write down who owns the input, when the copy is made and what an existing request may observe. Changing the environment is not proof that a running process picked up the new value.

## Check your work

Explain the behavior in your own words, including a failure that the happy path misses. Compare your observation with the public tests and record what you actually ran. Revisit the short-answer recall with guidance closed; assisted and repeated answers remain different evidence.
