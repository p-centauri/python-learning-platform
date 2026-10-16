## The idea in plain language

Operations such as len(obj) normally look up their special method on the object's type. Writing a same-named attribute on the instance is not a reliable way to change that operation. The example deliberately creates an instance __len__ entry: explicit attribute access sees it, but len still uses the class implementation. Many implicit special-method operations bypass the instance dictionary and custom __getattribute__ hooks; each operation still has its own documented rules.

A container interface makes promises. __len__ returns a nonnegative integer. __bool__ takes priority for truth testing when provided; otherwise length controls whether a container is empty. __getitem__ should make index bounds and slicing predictable. A Sequence implementation can inherit iteration, membership and reverse iteration from its length/index behavior. Those convenient mixins do not guarantee good performance: repeated expensive indexing can make iteration expensive.

Choose whether your collection is a snapshot or a view. A tuple copied from an input list records that moment's elements; clearing the original list should not change its length. But a tuple does not freeze mutable elements inside it. This lab's Reading and FeedKey values are frozen and contain immutable identity/value fields, which makes its snapshot meaningful. Snapshot construction consumes a borrowed iterable once and does not close it.

A count limit does not establish an arbitrary input time limit. The lab accepts at most 64 readings and observes the 65th to detect overflow. A borrowed iterator could block while producing an item. No API process runs that iterator. Keep repr useful for debugging without treating it as secure redaction, a parseable interchange format, or a stable public serialization contract. Use explicit structured data for interchange.

## Worked example

Run this trusted example locally and predict the output before execution.

```python
from collections.abc import Iterator, Sequence
from typing import overload

class Pair(Sequence[int]):
    def __len__(self) -> int:
        return 2
    @overload
    def __getitem__(self, index: int) -> int: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[int]: ...
    def __getitem__(self, index: int | slice) -> int | Sequence[int]:
        return (3, 7)[index]
    def __iter__(self) -> Iterator[int]:
        return iter((3, 7))

pair = Pair()
pair.__dict__["__len__"] = lambda: 99
print(getattr(pair, "__len__")(), len(pair))  # 99 2
print(list(pair), bool(pair))  # [3, 7] True
```

## Guided practice

Compare the two length calls and explain where each searches. Remove the instance entry and observe that explicit access then binds the class method. Check membership, negative indices and reversed iteration against the same two elements.

## Independent practice

Implement the Snapshot constructor in the lab while preserving its supplied length/index methods. Mutate the original input list, try an empty snapshot, and use an endless numbered generator to record exactly 65 pulls at overflow. Explain why this count bound cannot stop a blocked iterator.

## Check your work

A class method controls len under normal implicit lookup. Truth and iteration agree with the stored snapshot. Borrowed ownership, shallow copying and finite observation limits are stated plainly.

Continue to [Equality, hashing & immutable keys](/lessons/python-equality-hashing).
