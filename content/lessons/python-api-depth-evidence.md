Download the API depth starter from the linked project. It contains complete scaffolding, public tests and three unfinished functions: matches, verify and accept. Implement them in operations.py. The maintained teaching reference is excluded from the download. Use the earlier authenticated starters to build the fixed dependency chain before installing this package. The README gives the order and commands. A source import alone is insufficient: build the source archive and wheel, install them into a clean environment and run outside the source directory.

Run the offline cases first. They check finite tag parsing, HMAC tampering, freshness edges, strict event values and construction without a connection. Offline runs explicitly skip twelve PostgreSQL cases. Those skipped cases do not evaluate concurrency, transaction rollback, source compatibility or HTTP storage failures. Supply an explicitly disposable PostgreSQL DSN privately to run all cases. The fixture creates a generated schema at delivery_004, adds the receipt table, then drops that table, compares original source metadata and removes its generated schema. Never supply the academy database or a production store.

Run demo.py with a report output path. It serves the installed app on an owned ephemeral loopback socket and makes actual httpx requests. The report records 200/bodyless 304/changed 200, 401/403 without tags, two competing deliveries with one duplicate, altered/stale signatures, a signed invalid body, conflicting raw bytes, a real lock timeout and successful retry. It records two receipts and one fact because the later retry has a distinct delivery ID but the same reading. No outbox intent is invented. The owned server stops and checked-out connections return to zero.

Submit the installed version, exact commands, public case output, saved JSON, original regressions and a short design explanation. Add one independent case rather than copying the published assertions. Four manual criteria cover validators/permission, signature/input, receipt/failure/compatibility and installed observations. Checklists and reported test results are self-reported; self/human feedback is labelled separately. This finite local evidence does not certify Python expertise, full public API safety, production TLS/proxy limits, secret rotation or external exactly-once effects.

## Guided practice

Predict the printed value before running this small illustration. Then explain which part requires a real request or database observation.

```python
evidence = {"http_observed": True, "expert_certified": False}
print(evidence["expert_certified"])
```

## Independent practice

Finish the linked project with all tests and the installed loopback report. Add an independent cross-namespace or conditional-list regression and explain its expected outcome before running it. Save a draft, then submit a fixed artifact for manual review.

## Check your work

Check report JSON against actual requests and database counts. Redact DSNs/credentials. Show that generated schemas, sockets and connections are cleaned and old service contracts still pass.

Continue with the [API depth lab](/projects#python-api-depth). Record commands and outcomes; keep private credentials out of submitted evidence.
