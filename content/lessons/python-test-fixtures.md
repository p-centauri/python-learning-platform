## The idea in plain language

A fixture gives a test a named dependency. Pytest finds the parameter name in the test function, prepares that fixture, and supplies its value. This avoids repeating setup while keeping the dependency visible. Start with function scope: each test receives fresh state. Broader scope is useful for expensive resources, but shared mutation can make tests pass or fail depending on order.

A yield fixture separates preparation from cleanup. Put resource release in a finally block surrounding yield so cleanup runs even when the test fails. Cleanup must follow ownership: a fixture that created a temporary client should close it; a helper borrowing that client should not. If setup can fail before yield, acquire resources with context managers or register cleanup as each resource is acquired.

Parametrization runs one behavioral assertion for several named inputs. Choose cases from the contract: zero and the inclusive maximum, just outside the range, invalid types, and malformed separators. Ten nearly identical happy inputs add less evidence than one meaningful boundary failure. Count collected cases separately from test functions.

Fixtures are preparation, not assertions hidden in a large framework. Keep assertions near the behavior they explain. tmp_path supplies an isolated temporary directory; caplog captures actual log records. Neither proves production filesystem permissions or the reliability of an external logging service.

## Worked example

Run this small example locally, then explain the output in your own words.

Save this as `example.py` in an environment with pytest, then run `python -m pytest -q example.py`. It collects three cases from one test function. This is real fixture injection; do not call the fixture function yourself.

```python
from collections.abc import Iterator
import pytest

@pytest.fixture
def values() -> Iterator[list[int]]:
    numbers: list[int] = []
    try:
        yield numbers
    finally:
        numbers.clear()

@pytest.mark.parametrize("minimum,expected", [(0, 12), (5, 10), (11, 0)])
def test_total(values: list[int], minimum: int, expected: int) -> None:
    values.extend([2, 10])
    assert sum(value for value in values if value >= minimum) == expected
```

## Guided practice

In the starter, read the function-scoped readings fixture and the logger yield fixture. Temporarily make a test fail after changing the logger level. Run another test and check that cleanup restores the prior level. Use pytest -q to collect actual cases.

## Independent practice

Add a tmp_path fixture for an offline record file. Parameterize minimum values 0, 60000, -1 and 60001 with clear case IDs. Explain why a session-scoped mutable list would make the tests dependent on execution order.

## Check your work

Fresh fixtures eliminate state leakage. Cleanup is observable on failure paths. Your case table maps each input to a specific rule, and your reported count uses pytest collection rather than guessing from function names.

Continue to [Test doubles & patching the lookup site](/lessons/python-test-boundaries).
