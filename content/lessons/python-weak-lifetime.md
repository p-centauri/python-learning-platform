## The idea in plain language

A normal reference keeps an object available. A weak reference lets you find it while another owner keeps it alive, without becoming an owner. WeakValueDictionary helps find existing objects without forcing them to stay in memory. A miss is normal, so callers need a miss strategy.

Resolve once and keep the result locally. If it is not None, that normal reference keeps the object alive during use. Checking a weak reference and resolving again creates a gap where it can disappear. Apply the same rule to a weak registry's get operation.

Not every object supports weak references. Many user classes do; plain integers do not. Slots-based classes need appropriate support, such as a __weakref__ slot or weakref_slot on a compatible dataclass. State how unsupported values fail.

Weak references do not close sockets or roll back transactions. Garbage collection timing is not a cleanup schedule. Cycles may delay collection, and interpreter shutdown is another special situation. A test can request gc.collect for a known collectible fixture; that does not prove when every application object will disappear.

weakref.finalize can provide fallback notification, but its callback must not retain the target directly or indirectly. Passing a target's bound close method can retain it through the callback. Explicit scopes provide timely ownership instead. Finalizers cannot await asynchronous release.

The lab's WeakRegistry is non-owning lookup only. It preserves identity and returns None on a miss. It promises neither capacity nor thread safety and never calls close. Resource scopes remain cleanup owners even when the registry points to their values.

## Worked example

Run this trusted example locally and trace ownership and exit order.

```python
from dataclasses import dataclass
import gc
import weakref
@dataclass
class Item:
    value: int
item = Item(5)
reference = weakref.ref(item)
held = reference()  # Resolve once.
assert held is item
del item
gc.collect()
assert reference() is held
del held
gc.collect()
print(reference() is None)  # True for this collectible fixture.
```

## Guided practice

Identify all strong references. Explain why held keeps the object alive and weak lookup never calls close.

## Independent practice

Implement WeakRegistry. Test replacement, unsupported values, temporary strong lookup, collectible cycles and no implicit close. Add a slots-based weak-reference reproduction.

## Check your work

Lookup preserves identity while available and handles misses. Explicit scopes own cleanup; finalizer timing is not promised.

Continue to [Resource contracts & the scoped ownership lab](/lessons/python-resource-contracts).
