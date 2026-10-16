from dataclasses import dataclass
import re
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator


def field(value: str) -> str:
    if type(value) is not str or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", value, flags=re.ASCII) is None:
        raise ValueError("invalid identity field")
    return value


@dataclass(frozen=True)
class Datum:
    id: str
    revision: int
    value: int

    def __post_init__(self) -> None:
        field(self.id)
        if type(self.revision) is not int or not 1 <= self.revision <= 8:
            raise ValueError("invalid revision")
        if type(self.value) is not int or not 0 <= self.value <= 1000000:
            raise ValueError("invalid value")


@dataclass(frozen=True)
class Cursor:
    id: str
    revision: int

    def __post_init__(self) -> None:
        field(self.id)
        if type(self.revision) is not int or not 1 <= self.revision <= 8:
            raise ValueError("invalid cursor revision")


@dataclass(frozen=True)
class Receipt:
    observed: int
    inserted: int
    duplicates: int


@dataclass(frozen=True)
class Page:
    items: tuple[Datum, ...]
    next_cursor: Cursor | None


class AuthenticationRequired(Exception):
    pass


class PermissionDenied(Exception):
    pass


class ConflictingDatum(Exception):
    pass


class InputRow(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    id: str
    revision: Annotated[int, Field(ge=1, le=8)]
    value: Annotated[int, Field(ge=0, le=1000000)]

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        return field(value)


class BatchInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    items: Annotated[list[InputRow], Field(max_length=64)]


class ReceiptOutput(BaseModel):
    observed: int
    inserted: int
    duplicates: int


class CursorOutput(BaseModel):
    id: str
    revision: int


class PageOutput(BaseModel):
    items: list[InputRow]
    next_cursor: CursorOutput | None
