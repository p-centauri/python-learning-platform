## The idea in plain language

A dot can read stored data or run code. For ordinary instance access using Python's default rules, first find the class entry along its inheritance order. A data descriptor there has priority over the instance dictionary. Next comes a stored instance value, then a non-data descriptor or plain class value. A descriptor is an object that customizes access; properties and ordinary methods use this machinery.

A property with only a getter is still a data descriptor: its setter exists and rejects assignment. Putting the same public name in the instance dictionary does not override it. An ordinary function on a class is a non-data descriptor. Reading it through an instance normally binds that instance as self; an instance entry of the same name can shadow it.

If ordinary lookup raises AttributeError, the surrounding access machinery can try __getattr__. That includes AttributeError raised inside a property. A broad fallback can therefore conceal a property bug. Raise a domain exception for an actual failed operation, and reserve AttributeError for a missing attribute. __getattribute__ intercepts ordinary attribute access more broadly; an override must delegate carefully to avoid recursion. Its behavior can change the default rules described here.

Use vars(obj) to inspect stored entries, and inspect.getattr_static when you need to inspect an attribute without triggering descriptors or fallback hooks. Static inspection returns the stored object, such as a property, rather than its computed result. Classes with slots may lack an instance dictionary. These observations are debugging tools, not a promise that every object's storage or custom lookup has this shape.

## Worked example

Run this trusted example locally and predict the output before execution.

```python
from inspect import getattr_static

class Config:
    mode = "class"
    @property
    def limit(self) -> int:
        return 8

config = Config()
config.__dict__["mode"] = "instance"
config.__dict__["limit"] = 99
print(config.mode, config.limit)  # instance 8
print(isinstance(getattr_static(config, "limit"), property))  # True
```

## Guided practice

Draw the class entry and instance entry for each name. Explain why the same dictionary write affects mode but not limit. Compare config.limit with getattr_static(config, "limit") without treating the returned property as its computed value.

## Independent practice

Build a class with a getter that deliberately raises AttributeError and a __getattr__ fallback. Observe which result escapes. Replace the operational failure with ValueError and show that it propagates. Record the reproduction and explain why a broad fallback could hide a defect.

## Check your work

You can predict the default lookup order, distinguish stored from computed values, and identify when a custom hook changes the rules. Do not infer missing data solely from a successful getattr fallback.

Continue to [Descriptors & per-object validation](/lessons/python-descriptors).
