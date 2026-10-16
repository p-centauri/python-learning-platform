## The idea in plain language

Equality answers whether two values represent the same thing under a declared contract. Identity with is answers whether they are the same object. Distinct keys may be equal and must work interchangeably in a dictionary. A hash helps choose where to search; equality still decides whether a matching candidate is the right key.

Equal hashable objects must have equal hashes. Unequal values can have equal hashes, and Python handles those collisions. Keep equality fields stable while the key is stored. If an identity field changes after insertion, dictionary lookup can use a different hash and fail unexpectedly. This lab uses frozen keys containing two validated strings. Frozen dataclasses containing lists would not magically make those lists immutable or hashable.

Return the singleton NotImplemented when your __eq__ does not support an operand. Python can try the other comparison implementation; subclass dispatch may give the subclass priority. Returning False immediately can block useful reverse comparison. If neither side supports equality, == ultimately falls back to identity. NotImplemented is a value returned by a comparison, whereas NotImplementedError is an exception for unfinished behavior. Do not convert the singleton to bool.

The example restricts comparisons to the same concrete type and compares both fields. Extending a value class with more state requires an explicit equality/hash design rather than assuming inherited methods include the new state. Defining __eq__ without a compatible __hash__ normally makes a mutable-style user class unhashable. Dataclass generation rules depend on eq and frozen settings; inspect the documented configuration. Hash results, especially those involving strings, are not a cross-process storage ID. Use the validated fields themselves for durable identity and explicit serialization.

## Worked example

Run this trusted example locally and predict the output before execution.

```python
from dataclasses import dataclass
from types import NotImplementedType

@dataclass(frozen=True, eq=False)
class Tag:
    namespace: str
    name: str
    def __eq__(self, other: object) -> bool | NotImplementedType:
        if not isinstance(other, Tag) or type(other) is not type(self):
            return NotImplemented
        return (self.namespace, self.name) == (other.namespace, other.name)
    def __hash__(self) -> int:
        return hash((self.namespace, self.name))

a, b = Tag("feed", "api"), Tag("feed", "api")
print(a is b, a == b, hash(a) == hash(b))  # False True True
print({a: 12}[b])  # 12
print(a.__eq__("feed/api") is NotImplemented)  # True
```

## Guided practice

Use two namespaces with the same name and show that they remain different keys. Assert equal hashes only for equal values; do not require every unequal value to have a different hash. Add a foreign operand whose comparison accepts Tag and observe reverse dispatch.

## Independent practice

Implement FeedKey equality and hashing in the lab. Verify dictionary lookup with a distinct equal instance, frozen assignment, wrong operand handling and distinct namespaces. Explain why hash(key) is unsuitable as the permanent database identity for a future ingestion service.

## Check your work

Equality and hashing use exactly the same stable fields. Unsupported comparison returns NotImplemented. A successful dictionary example establishes the finite key contract, not universal correctness of all subclass designs.

Continue to [Object contracts & the feed snapshot lab](/lessons/python-object-contracts).
