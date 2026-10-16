A release report needs enough detail to explain a failure without becoming another channel for private data. Raw prompts, retrieved excerpts, tool arguments and exception messages can contain secrets or personal information. Copying them into a public log can leak data even when the returned answer was correctly blocked. Review the report boundary as part of the evaluation.

The local observation records case and candidate IDs, full scoped source keys, source digests, outcome names, actual request charges/counts, local effect/replay facts and model/prompt/schema versions. It does not record raw source text, query text, URLs, labels or private exception messages. Exact rational metrics expose their numerators and denominators. This gives a reviewer a finite trail to reproduce the controlled experiment without copying its contents into every report.

Private synthetic markers are planted in restricted and foreign sources. The harness checks actual selected/request/answer data internally for exposure, then records a boolean privacy failure. Public serialization is tested to exclude those markers and malicious source text. These markers are artificial test strings, not real credentials. Zero marker leaks only establishes the finite tested channel; unknown secret formats and real system logs need separate policies.

A digest is useful for identity, but it is not anonymization. Full source keys and effect metadata can themselves be sensitive in a deployed system. The original fixture has invented identities. Production retention, access, redaction and deletion rules must cover metadata too. Do not log broad service tokens or database credentials for debugging.

The guarded demo owns temporary source/note databases and removes them after the run. The academy stores learner-reported artifacts and manual reviews privately; it does not execute uploads. Keep logging claims limited to the actual report and channels observed. A useful trace explains what happened without pretending that every possible leak has been ruled out.

## Guided practice

Predict the printed result, then explain which evaluation boundary this small illustration leaves untested.

```python
public_report: dict[str, object] = {"reason": "forbidden", "calls": 1}
print("source_text" in public_report)
```

## Independent practice

Serialize only the stated safe observation fields and assert that raw malicious/private fixture text is absent. Explain one production metadata/retention risk outside this fixture.

## Check your work

Record actual versions and counts without prompts or secrets. State why hashes and zero synthetic-marker leaks are limited evidence.

Use the [AI release evaluation project](/projects#ai-evaluation). Record commands, versions and failures. Reported tests and manual review remain separate from mastery.
