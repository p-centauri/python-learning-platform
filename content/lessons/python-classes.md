## Put state on the object that owns it

This is lesson 1 of 5 in object design and typing. Read [references and ownership](/lessons/python-ownership) first. A class describes objects with related data and behavior. Use one when several operations need to protect the same state. A function remains a good choice when it only transforms its arguments.

Imagine two inboxes. Each must keep its own task titles. A list on the class would be shared; a list created in `__init__` belongs to that new inbox. `self` is the object receiving the method call. Python passes it when you write `inbox.add(...)`; it is not a special global variable.

```python
class Inbox:
    kind = "personal"  # Shared label, not a place for per-inbox tasks.

    def __init__(self) -> None:
        self._titles: list[str] = []

    def add(self, title: str) -> None:
        if not title.strip():
            raise ValueError("title must not be blank")
        self._titles.append(title.strip())

    @property
    def count(self) -> int:
        return len(self._titles)

    def titles(self) -> tuple[str, ...]:
        return tuple(self._titles)

first = Inbox()
second = Inbox()
first.add(" Read traceback ")
assert first.count == 1
assert second.count == 0
before = first.titles()
first.add("Write regression test")
assert before == ("Read traceback",)
assert first.count == 2
```

`count` is a property: callers read `first.count`, while Python computes its value. This avoids a second counter that could drift away from the list. The leading underscore in `_titles` asks callers to treat it as internal. It does not provide access control. Returning a tuple here prevents callers from editing the internal list through the returned result. Because these elements are strings, there is no mutable nested object to leak.

## Guided practice

Save the example and run it. Create a third inbox and add two titles. Check all three counts. Then deliberately move the empty list to the class body and remove the assignment in `__init__`. Observe which assertion fails. Restore the correct ownership rule before continuing.

Try a blank title. The exception is useful: the method refuses a state the object promises not to contain. Our annotated method assumes its caller passes a string; outside input needs a separate runtime check, taught later in this module.

## Independent task

Add `remove(title: str) -> None`. Strip the argument, remove only the first matching title, and raise `ValueError` when no match exists. Keep the same per-object ownership. Do not expose `_titles` for callers to change directly.

Write tests for two equal titles, a missing title and a second inbox remaining unchanged. Describe when a list of titles plus plain functions would be simpler than this class.

## Check your work

After adding the same title twice, one removal should leave one title. A failed removal must leave the inbox unchanged. A previously returned tuple should still describe the old snapshot. These tests check observable promises instead of depending on the private attribute name.

[Next: dataclasses and value objects](/lessons/python-dataclasses)
