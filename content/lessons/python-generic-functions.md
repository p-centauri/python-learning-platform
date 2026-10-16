## The idea in plain language

A generic function keeps a relationship between types across different calls. If it accepts an item of type T and returns that same item, the caller should retain T rather than receive an unhelpful object or unchecked Any. The function can work for several types while still giving each caller a precise result.

The example uses Python's type-parameter syntax, available since 3.12 and supported by this academy's 3.13+ baseline. T is local to that generic definition. The older spelling declares T = TypeVar("T") before using it in annotations. The lab uses that spelling where explicit variance and ParamSpec make the relationship easier to inspect. Neither spelling converts or validates runtime values.

A bound restricts a parameter to a base type while preserving an accepted subtype: a type variable bound to Animal can retain Dog. Constraints such as TypeVar("Text", str, bytes) restrict a related use to the permitted alternatives; the checker may promote a subclass to its matching constrained base. Do not replace a relationship with a broad union when the arguments must agree, and do not add a bound unless the implementation needs that interface.

A return-only type parameter with no way to establish its value is usually an impossible promise. A function cannot manufacture any type a caller chooses merely because an annotation says T. A mapper is a concrete way to relate input T to output U: the supplied callable actually produces U. Generic classes likewise preserve their element interface, but that interface's mutation policy matters. In the next lesson we use producer and consumer rules to decide which substitutions are safe. These static relationships help checked callers; runtime validation still belongs at external boundaries.

## Worked example

Run this trusted example locally and compare actual behavior with its static contract.

```python
from typing import assert_type

def pair[T](item: T) -> tuple[T, T]:
    return item, item

class Box[T]:
    def __init__(self, value: T) -> None:
        self._value = value
    @property
    def value(self) -> T:
        return self._value

numbers = pair(3)
text = Box("api").value
assert_type(numbers, tuple[int, int])
assert_type(text, str)
print(numbers)  # (3, 3)
print(text.upper())  # API
```

## Guided practice

Trace T separately for the integer pair and the string box. Change the integer to a string and inspect the checker result before running. Explain why assigning pair(3) to tuple[str, str] should be rejected even though pair itself is reusable.

## Independent practice

Implement map_rows in the typed transformation lab. Relate iterable element T, mapper argument T and mapper result U to tuple[U, ...]. Preserve the supplied count/ownership/error contract, then compare a successful runtime case with a rejected wrong-result assignment.

## Check your work

A generic annotation records an actual relationship the implementation preserves. You can explain bounds versus constraints and avoid Any or a cast that would erase the evidence. The type checker does not enforce the element count or stop a blocked mapper.

Continue to [Variance & read-only interfaces](/lessons/python-variance).
