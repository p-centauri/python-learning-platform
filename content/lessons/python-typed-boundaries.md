## The idea in plain language

External input can violate the types your checked source expects. Annotating the boundary as object makes you prove which operations are safe before indexing or calling methods. Any instead permits unchecked operations and can spread through a public API until useful errors disappear. Some libraries return Any; deliberately assign that input to object at the boundary and validate it.

cast tells the checker to trust an asserted type. It returns the same runtime object and performs no validation or conversion. Use it only when another concrete argument justifies the claim and ordinary narrowing cannot express that argument. A cast is not a repair for a number arriving where your code expects text.

A TypedDict describes a dictionary's expected field types for checked callers; it is not a JSON validator or an immutable domain object. A type alias gives another spelling to the same type. NewType can separate logical identities for checked callers but likewise does not enforce ranges, authenticate an ID or create a new runtime value class. Input validation has to check the actual shape, exact types when required, and business rules before constructing accepted values.

In our lab the supplied guard checks exact dictionary keys and string/integer field types. decode_row still needs that current check, and the frozen Row validates bounded ASCII IDs and inclusive numeric limits. Booleans inherit from int, so an exact-int contract rejects them deliberately. Copy accepted immutable field values into a fresh Row rather than keeping the caller's mutable dictionary. No coercion, invented defaults, unbounded validation framework or general concurrent-mutation guarantee is introduced.

## Worked example

Run this trusted example locally and compare actual behavior with its static contract.

```python
from typing import NewType, cast

raw: object = {"id": 3}
pretend = cast(dict[str, str], raw)
try:
    print(pretend["id"].upper())
except AttributeError:
    print("cast did not validate")

def limit_from(value: object) -> int:
    if type(value) is not int:
        raise TypeError("exact integer required")
    if not 0 <= value <= 64:
        raise ValueError("outside range")
    return value

UserId = NewType("UserId", int)
print(UserId(3) == 3, limit_from(4))  # True 4
```

## Guided practice

Explain why the cast passed a static assumption but the actual method call still failed. Trace limit_from(True) separately from limit_from(65): the first violates exact type and the second violates the value range.

## Independent practice

Implement decode_row using the supplied structural guard and Row constructor. Reject bad shape/types without coercion, reject invalid domain values, and show caller dictionary mutation cannot change the resulting Row. Record a positive runtime case and a negative unchecked-object fixture separately.

## Check your work

You can identify which evidence came from the checker and which from real validation. Cast, TypedDict, aliases and NewType do not authorize or validate external data.

Continue to [Typed library interfaces & the transformation lab](/lessons/python-typed-interfaces).
