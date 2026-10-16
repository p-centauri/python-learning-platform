"""Checked statically; this file is never executed by the checker."""

from collections.abc import Sequence
from typing import TypeIs, assert_type
from academy_typed_transforms import (
    Consumer,
    Row,
    RowPayload,
    Valued,
    decode_row,
    first,
    is_row_payload,
    map_rows,
    watch_call,
)


def label(value: int, /, *, prefix: str = "row") -> str:
    return f"{prefix}-{value}"


def observe(event: str) -> None:
    pass


wrapped = watch_call(label, observer=observe)
assert_type(wrapped(3, prefix="api"), str)
assert_type(map_rows([1, 2], str), tuple[str, ...])
assert_type(first([1]), int | None)
assert_type(first([1], default="missing"), int | str)
assert_type(first([1], default=0), int)
assert_type(decode_row({"id": "api", "value": 1}), Row)


class Animal:
    pass


class Dog(Animal):
    pass


class DogValue:
    @property
    def value(self) -> Dog:
        return Dog()


dog_value: Valued[Dog] = DogValue()
animal_value: Valued[Animal] = dog_value
assert_type(animal_value.value, Animal)
dogs: list[Dog] = [Dog()]
animals: Sequence[Animal] = dogs


def accept_any(value: object, /) -> None:
    pass


all_consumer: Consumer[object] = accept_any
text_consumer: Consumer[str] = all_consumer
text_consumer("event")


def is_text(value: object) -> TypeIs[str]:
    return isinstance(value, str)


def narrowed(value: str | int, payload: object) -> None:
    if is_text(value):
        assert_type(value, str)
    else:
        assert_type(value, int)
    if is_row_payload(payload):
        assert_type(payload, RowPayload)
        assert_type(payload["value"], int)
    else:
        assert_type(payload, object)
