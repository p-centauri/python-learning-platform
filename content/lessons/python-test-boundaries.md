## The idea in plain language

A test double replaces a dependency so a test can control inputs and failures. A fake has a small working implementation, such as a byte stream that records reads and closure. A mock can record calls and return configured values. Both are tools; neither is automatically proof that the real contract works.

Choose the boundary that makes the test deterministic. For ingestion, use an HTTPX fake transport while retaining the real response owner and parser. For reporting, pass a reporter function that records input identity and returns a known object. If you replace the function you intended to test, your assertion often checks only the replacement setup.

Patch the location from which the code reads a dependency. If a module imported a function into its own name, changing the original defining module later may leave that local name unchanged. With `import module`, the lookup is an attribute on that module. Pytest monkeypatch restores changes after the test, including when an assertion fails. A patch of a shared module attribute can still affect other code during the test, so keep its lifetime narrow.

Use observable outcomes: values returned, exception identity, how many records were consumed, and whether owned resources closed. Avoid asserting every private helper call. Such tests break during harmless refactors and can still miss real errors. Deterministic inputs remove the need for network access or timing sleeps.

## Worked example

Run this small example locally, then explain the output in your own words.

```python
from collections.abc import Callable

def fetch_total(read: Callable[[], list[int]]) -> int:
    return sum(read())

calls: list[str] = []
def fake_read() -> list[int]:
    calls.append("read")
    return [2, 3]

print(fetch_total(fake_read), calls)  # 5 ['read']
```

## Guided practice

Use the starter monkeypatch test to observe the real regex call at policy.re.fullmatch. Keep the original implementation available so validation still happens. Compare this with replacing parse_selector itself; explain why the latter skips the behavior you need to verify.

## Independent practice

Create a source that yields one valid reading and then raises a specific exception. Run the real filter and logging wrapper. Assert the original exception escapes and no success event is emitted. Explain which network behavior this local test cannot prove.

## Check your work

You can name the real behavior and the controlled dependency in each test. At least one failure occurs after useful work starts. Restored patches and independent fixtures keep later tests unaffected.

Continue to [Safe logging with observable outcomes](/lessons/python-safe-logging).
