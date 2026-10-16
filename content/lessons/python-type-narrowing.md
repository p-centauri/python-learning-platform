## The idea in plain language

Narrowing means the checker knows a more specific type inside a branch because a condition established it. An isinstance test is the familiar example. Custom predicates can declare how their successful checks should affect a caller, but the declaration must honestly match the test.

TypeGuard narrows the true branch to its stated target. It can express a more specific container shape even where ordinary invariant container subtyping would not allow assignment. Its false branch does not automatically exclude that target. A predicate may recognize only some valid values of that target, such as a structural dictionary check; a failed check therefore does not always tell you what the value is.

TypeIs, available in the standard library on our Python 3.13+ baseline, narrows both branches: compatible target possibilities in the true branch, and excluded target possibilities in the false branch. Its target must be compatible with the input type, and the predicate must recognize all and only that target. An int test that returns false for negative integers is not an honest TypeIs[int]: negative integers are still integers. Use a separate business-rule check rather than claiming their type disappeared.

Neither declaration makes the checker prove the predicate body is logically correct. Nor does a guard freeze mutable input. Another alias, a callback or concurrent work may change checked contents after the check. Validate at the actual boundary, copy accepted immutable values when the contract needs stability, and state ownership. The lab separates a structural TypeGuard from the Row's value rules and rechecks payloads at decoding. There is no await or callback between that decoder's shape check and value construction, and no claim of general thread safety.

## Worked example

Run this trusted example locally and compare actual behavior with its static contract.

```python
from typing import TypeGuard, TypeIs, assert_type

def is_text(value: object) -> TypeIs[str]:
    return isinstance(value, str)

def is_numbers(value: object) -> TypeGuard[list[int]]:
    return isinstance(value, list) and all(isinstance(item, int) for item in value)

def show(value: str | int) -> str:
    if is_text(value):
        assert_type(value, str)
        return value.upper()
    assert_type(value, int)
    return str(value + 1)

payload: object = [1, 2]
if is_numbers(payload):
    assert_type(payload, list[int])
    print(sum(payload))  # 3
print(show("api"), show(4))  # API 5
```

## Guided practice

Trace both branches of show. Explain why a predicate returning false for negative ints cannot use TypeIs[int] to promise the false branch excludes integers. For a TypeGuard, keep the unchanged false branch visible.

## Independent practice

Run the lab’s TypeGuard/TypeIs positive fixtures and incompatible-TypeIs rejection. Check a dictionary, mutate it through another alias, and demonstrate that decode_row must validate its current shape. Do not claim a guard prevents future mutation.

## Check your work

A predicate earns narrowing through its real test, and its claimed target is honest. You can describe which branches change and why copying/ownership matter separately.

Continue to [Unknown input, casts & runtime validation](/lessons/python-typed-boundaries).
