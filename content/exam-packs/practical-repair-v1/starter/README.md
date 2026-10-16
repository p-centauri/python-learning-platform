# Practical engineering repair exam

This is an intentionally broken, loopback-only teaching application. Do not deploy it or give it real credentials/data. Target study time: 4–6 hours, advisory and resumable.

1. Read CONTRACT.md and inspect core.py, server.py and Dockerfile.
2. Run `python -m unittest discover -s tests -v`. The original starter is expected to fail all eight public regressions. Keep this baseline output.
3. Repair the standalone standard-library core. Add your own regression tests. Run the application locally with `python server.py` using synthetic cases only.
4. Save the exact core.py source in the academy practical attempt, then run the isolated checks. Twenty-three finite checks cover eight public and fifteen additional private cases. The API never executes this code.
5. Write the seven review responses, including real query/lifetime observations, HTTP/Docker fixes, remaining limits and a fixed repository revision. Failures can be submitted honestly.
6. Submit to freeze source, responses and exact matching run. Open the review workspace, invite a registered account and address feedback in a separate revision.

The private suite checks the offline core only. The HTTP shell, Docker release, architecture, PostgreSQL concurrency, real brokers, learned-model quality and operations require observed evidence and human review. A passed suite is not a production certificate. Expected private outputs and maintained implementations are never in this pack.
