## The idea in plain language

A public interface includes call shape, result type, errors, effects and ownership. Changing a default or returning a tuple where callers expect an integer can break clients even if your internal tests still pass. Write down the compatibility promise and test actual old callers.

An adapter can keep an old entry point working while moving implementation to a new one. Preserve supported arguments and delegate once. Warn at the caller's location with an appropriate stacklevel. The lab defines a supported deprecated legacy_get adapter as an exercise; it does not invent a historical public release.

DeprecationWarning is normally filtered in many imported-code contexts. Tests should enable it and inspect category/message/location. Users can configure warnings as errors; because this lab warns before delegating, that configuration prevents the delegate's effects. Document this observable behavior.

Static tests verify that supported typed callers still make sense; runtime tests verify results, error propagation and effects. Neither substitutes for the other. A version number does not prove compatibility. State a supported interpreter range, artifact dependencies, migration path and the release where removal is intended when you actually have such a policy.

Build and install the real artifact outside source. Quiet imports, exported names, typing markers, resource files and old call examples are part of evidence. Avoid hiding breakage with broad casts or silent fallbacks. The lab stores manual review of actual reported output, separate from objective grading or expertise.

## Worked example

Save this trusted example as example.py and run it locally. Keep profiling/memory instrumentation separate from benchmark timing.

```python
import warnings
def parse_current(text: str) -> int:
    return int(text)
def parse_legacy(text: str, /) -> int:
    warnings.warn("Use parse_current", DeprecationWarning, stacklevel=2)
    return parse_current(text)
with warnings.catch_warnings(record=True) as observed:
    warnings.simplefilter("always", DeprecationWarning)
    result = parse_legacy("7")
print(result, len(observed))
print(observed[0].category is DeprecationWarning)
```

## Guided practice

Identify the preserved old call/result contract and caller warning. Explain filtered warnings versus warnings-as-errors before delegation.

## Independent practice

Implement legacy_get and test old callers, identity/hits, failure propagation, warning location and warnings-as-errors. Show strict typed installed callers.

## Check your work

Compatibility evidence covers call shapes and runtime effects. Do not claim that a version label or warning alone preserves callers.

Continue to [Measurement contracts & the reviewed cache lab](/lessons/python-measurement-contracts).
