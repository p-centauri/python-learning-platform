## Give a service the helper it needs

This is lesson 3 of 5. Composition means building an object from other objects. A task service can use a store without being a kind of store. Passing that store into the constructor lets the caller choose where data lives. This is often called dependency injection; here it is just an ordinary argument.

```python
class MemoryTitles:
    def __init__(self) -> None:
        self._values: list[str] = []

    def add(self, title: str) -> None:
        self._values.append(title)

    def all(self) -> tuple[str, ...]:
        return tuple(self._values)

class TitleService:
    def __init__(self, store: MemoryTitles) -> None:
        self._store = store

    def create(self, title: str) -> None:
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("title must not be blank")
        self._store.add(cleaned)

store = MemoryTitles()
service = TitleService(store)
service.create(" Inspect request ")
assert store.all() == ("Inspect request",)
try:
    service.create("   ")
except ValueError:
    pass
else:
    raise AssertionError("blank title was accepted")
assert store.all() == ("Inspect request",)
```

The service decides what a valid title is. The store keeps accepted titles. Notice the order: validation happens before writing. A rejected call must not leave an entry behind. Keep this promise visible in tests.

The example uses a concrete store annotation for now. Later we will describe just the required operations with a protocol. This avoids making the service depend on every detail of a storage implementation.

## Composition and inheritance answer different questions

Inheritance can be useful when a new class genuinely fits the parent's promises. It is a poor fit when a class only wants to borrow a helper method. If `ReadOnlyStore` inherits an `add` method but always raises an unsupported-operation error, callers expecting a writable store may fail unexpectedly. A separate read-only interface describes that limit more clearly.

A service holding a store can change helpers without pretending to be the helper. Avoid building a large hierarchy before there are real behaviors to share. Small functions and two cooperating classes are enough for this module's project.

## Guided practice

Construct two services with separate stores. Add a title through the first and confirm the second store stays empty. Then deliberately give both services the same store. Confirm that they share entries. Neither outcome is magic: the caller selected the ownership boundary.

## Independent task

Add `titles()` to the service so callers need not know its storage field. Then add a `PrefixService` that holds a `TitleService` and adds a fixed prefix before creating a title. Use composition instead of inheritance. Document whether an originally blank title is allowed after prefixing; test your chosen rule.

## Check your work

Tests should exercise the real service and inspect observable results. Replacing `create` with a mock returning success would skip the validation you meant to test. Explain where an exception from storage should go: this small service lets it reach the caller, so a failed write never looks successful. Database transactions and retry policies require additional design later.

[Next: type hints and input validation](/lessons/python-type-hints)
