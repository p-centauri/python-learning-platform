## The idea in plain language

A regular expression describes a text pattern. It is useful for a small, explicit grammar such as prefix:minimum. It is a poor substitute for a whole parser, authorization check or application policy. Start by writing the accepted shape in plain language, then convert each part into a pattern you can explain.

Use re.fullmatch when the whole input must match. A search can find an acceptable fragment inside an otherwise invalid string. Use [0-9] for this ASCII contract: Python's default \d also accepts Unicode decimal digits. Reject whitespace rather than silently stripping it when the contract says exact input. Make the maximum length explicit before matching.

Syntax and meaning are separate. The pattern can recognize a five-digit number, but 60001 still violates our 0–60000 domain range. Match first, convert the captured ASCII digits, then check the range. Generic RuleError messages avoid reflecting rejected data into logs or UI. This deliberately simple bounded pattern is not a general claim of protection against every expensive regex.

The lab combines previous ideas without changing the published ingestion parser. Its read-only Reading protocol accepts the earlier frozen Record structurally. The filter borrows that stream; the HTTP owner still handles acquisition and closure. The wrapper observes the complete report outcome. This connection lets you test real composition while keeping each responsibility small.

## Worked example

Run this small example locally, then explain the output in your own words.

```python
import re

def parse_rule(text: str) -> tuple[str, int]:
    if len(text) > 22:
        raise ValueError("Invalid selector")
    match = re.fullmatch(r"([a-z][a-z0-9-]{0,15}):(0|[1-9][0-9]{0,4})", text)
    if match is None:
        raise ValueError("Invalid selector")
    prefix, digits = match.groups()
    minimum = int(digits)
    if minimum > 60000:
        raise ValueError("Invalid selector")
    return prefix, minimum

print(parse_rule("api:10"))  # ('api', 10)
```

## Guided practice

Read the exact starter contract, then implement parse_selector, make_selector and logged_report. Keep apply_policy lazy. Run every public case, the strict type check and lint. The input boundary must reject non-strings before calling regex methods.

## Independent practice

Add two regressions with explanations, build a wheel and install it outside the source tree. Connect prior ingestion records through a typed reporter adapter. Submit the artifact link, reported tests, design explanation and known gaps through the project review workflow.

## Check your work

Explain why 01, a Unicode digit, a trailing newline and 60001 are rejected for different reasons. Public tests check a bounded contract; reviewer judgment remains manual, and neither a checklist nor reported tests award mastery. Continue async teaching only after you can explain these ownership and outcome boundaries.

Open the [Feed filtering & test-design lab](/projects#python-feed-policy) and submit evidence for manual review. Continue to [Coroutines & the event loop](/lessons/python-coroutines) for bounded async work and cleanup.
