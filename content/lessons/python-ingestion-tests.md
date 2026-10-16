## Test the boundary without replacing its behavior

Use a fake transport to control the network, while exercising your real parser and resource owner. This is lesson 8 of 8. Mocking open_feed to return a fixed list would bypass the code whose cleanup and validation you need to prove.

The [installable ingestion lab](/projects#python-ingestion-package) has 28 public tests. They observe reads and closure, split records across chunks, reject invalid types, preserve causes, check actual body bytes, refuse redirects and run the offline CLI. These tests cover a finite contract; a reviewer still checks the implementation and additional evidence.

## Make failure visible at the right point

```python
from collections.abc import Iterator

def late_failure() -> Iterator[int]:
    yield 2
    raise ValueError("later input failed")

published: list[int] = []
try:
    total = sum(late_failure())
except ValueError:
    pass
else:
    published.append(total)
assert published == []
```

The success result is published only after full consumption. A test with just valid data misses this distinction. Also test no consumption, early exit, parser failure, transport failure and consumer failure. Verify state directly; forcing garbage collection does not establish timely cleanup.

## Review the whole installed package

Download the [starter and public tests](/api/projects/python-ingestion-package/starter). Implement its three learner functions. Use the real interfaces and preserve the exact contract. Run the public suite, lint and strict types; add a late-failure case that observes empty CLI stdout. Build wheel and source distribution, install outside the checkout, inspect resources, and execute both command forms.

## Guided practice

Follow one successful request through client, response, chunk reader, parser, summary and output. Repeat with an exception after the first record. Write down who closes each object. Test a borrowed source separately from an owned response.

## Independent project

Submit a fixed repository revision, reported commands/output, two new regressions and a short explanation of input bounds and URL trust. Ask an existing reviewer account to inspect that revision. Revise it if feedback identifies missing failure evidence. Review results remain manual judgment; project checkboxes are self-reported.

## Check your work

Explain what MockTransport cannot test: real DNS/TLS, deployment routing, total deadlines and server-side destination isolation. This package does not yet write to PostgreSQL or retry jobs. The next teaching work connects validated ingestion to transaction-safe backend services and bounded workers; advanced Python and applied AI coverage also remain in the saved plan.

Continue to [Closures & late binding](/lessons/python-closures) to add independent filtering and testable reporting.
