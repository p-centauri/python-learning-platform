## The idea in plain language

A descriptor belongs to a class, so many instances use that one descriptor object. Store each instance's actual value on that instance. Otherwise changing one object's field can unexpectedly change another object's value. __get__ reads an instance value; __set__ controls assignment. Defining __set__ makes it a data descriptor, so a same-named public entry in the instance dictionary cannot shadow it under default lookup.

Class creation calls __set_name__ with the owner and field name for attributes that implement it. This gives a reusable field a storage name. Inheritance reuses the existing descriptor; it does not call __set_name__ again just because a subclass inherits that field. Attaching an attribute after class creation does not automatically deliver this notification. Keep this lab's fields declared in the class body and use a separate descriptor per field.

Class access passes None as the instance. Return the descriptor itself there so Budget.limit can be inspected. For an instance, a missing stored value raises AttributeError rather than silently returning zero. Validate the proposed value before replacing a previous good value. Since bool is a subclass of int, an exact-integer contract must reject booleans explicitly.

The example below fixes one storage name to keep the first trace small. The lab generalizes it to two independently named fields and adds bounded validation. Overloads tell a type checker that class access returns a descriptor while instance access returns an int. They describe the interface; runtime checks still enforce inputs. A property is usually simpler for one field. A descriptor earns its complexity when several fields need the same access policy; it is not an authorization boundary against Python code that can change private storage.

## Worked example

Run this trusted example locally and predict the output before execution.

```python
from __future__ import annotations
from typing import overload

class Limit:
    @overload
    def __get__(self, obj: None, owner: type[Quota] | None = None) -> Limit: ...
    @overload
    def __get__(self, obj: Quota, owner: type[Quota] | None = None) -> int: ...
    def __get__(self, obj: Quota | None, owner: type[Quota] | None = None) -> Limit | int:
        return self if obj is None else obj._limit
    def __set__(self, obj: Quota, value: int) -> None:
        if type(value) is not int:
            raise TypeError("integer required")
        if not 0 <= value <= 64:
            raise ValueError("outside range")
        obj._limit = value

class Quota:
    _limit: int
    limit = Limit()
    def __init__(self, value: int) -> None:
        self.limit = value

a, b = Quota(2), Quota(5)
a.limit = 7
print(a.limit, b.limit)  # 7 5
print(isinstance(Quota.limit, Limit))  # True
```

## Guided practice

Trace the descriptor object once and draw two separate Quota objects. Write a failing assignment of 65 and verify that the old value survives. Explain which method receives the owner instance, and why setting self.value on Limit would share data.

## Independent practice

Download the feed-object lab from Projects. Implement BoundedInt.__get__ and __set__ using the supplied binding name and each Budget._values dictionary. Test two fields on two instances, subclass access, a missing field, booleans and inclusive endpoints before continuing.

## Check your work

Class access returns the shared descriptor; values stay per instance and per field. Rejected updates preserve earlier data. Do not claim private dictionaries prevent deliberate tampering.

Continue to [Inheritance order & cooperative super](/lessons/python-cooperative-mro).
