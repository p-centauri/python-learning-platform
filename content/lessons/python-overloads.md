## The idea in plain language

An overload describes a supported call shape to the type checker. Several overload declarations are followed by one implementation that actually runs. They do not choose runtime behavior by annotation. The implementation must accept those shapes and return what each declaration promises.

The example distinguishes a call with no explicit default from a call with a default of type U. Without a default, empty input can return None, so callers see T | None. With a supplied default they see T | U. A default string for integer input keeps both possibilities visible. Even when a particular list happens to be nonempty, this general interface does not promise every future call returns an integer.

The implementation accepts the combined possibilities and tests the actual sequence length. It preserves the selected object and avoids materializing the whole input. Ordered overloads need careful review: a narrow case normally comes before a broad compatible case. Overlapping declarations with incompatible return promises can make a caller's result unsound. Use a union when it already states the complete simple relationship; add overloads when different argument shapes genuinely imply different result types.

The checker can reject assigning an optional result directly to int. That does not prove runtime indexing, ownership or exception behavior. Test empty and nonempty input, None and non-None defaults, object identity, and a borrowed sequence whose index operation can fail. Do not hide an absence case with cast. The lab's positive assert_type calls and rejected optional-result assignment check the published static interface alongside its public runtime cases.

## Worked example

Run this trusted example locally and compare actual behavior with its static contract.

```python
from collections.abc import Sequence
from typing import TypeVar, assert_type, overload

T = TypeVar("T")
U = TypeVar("U")
@overload
def first(rows: Sequence[T], /) -> T | None: ...
@overload
def first(rows: Sequence[T], /, *, default: U) -> T | U: ...
def first(rows: Sequence[T], /, *, default: U | None = None) -> T | U | None:
    return default if len(rows) == 0 else rows[0]

possible = first([5])
with_default = first([5], default="missing")
assert_type(possible, int | None)
assert_type(with_default, int | str)
print(first([], default="missing"))  # missing
print(possible)  # 5
```

## Guided practice

Compare the static types with the actual values printed by this invocation. Replace the nonempty list with an empty typed integer sequence and explain why the absence branch already belonged in the interface.

## Independent practice

Implement first in the lab. Preserve first/default identity and use length/index zero without iteration. Run its positive overload calls and negative int assignment, then write a caller that handles None rather than casting it away.

## Check your work

You can name the call shape and its possible return values. One implementation executes the behavior. Overloads neither dispatch at runtime nor prove the sequence is nonempty.

Continue to [TypeGuard, TypeIs & honest narrowing](/lessons/python-type-narrowing).
