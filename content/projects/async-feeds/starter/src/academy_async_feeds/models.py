from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
import re
from typing import Protocol, TypedDict
from urllib.parse import urlsplit

MAX_LINE_BYTES = 1024
MAX_BODY_BYTES = 8192
MAX_SOURCES = 16


@dataclass(frozen=True)
class Record:
    id: str
    value: int


@dataclass(frozen=True)
class Source:
    label: str
    url: str


class BatchReport(TypedDict):
    sources: int
    count: int
    total: int


class Opener(Protocol):
    def __call__(self, source: Source, /) -> AbstractAsyncContextManager[AsyncIterator[Record]]: ...


class ConfigError(ValueError):
    """Invalid bounded job configuration, without raw input in its message."""


class RecordError(ValueError):
    """Invalid input at a one-based physical line."""


class FeedError(ValueError):
    """Invalid response or incomplete batch."""


def validate_source(source: Source) -> None:
    if (
        not isinstance(source, Source)
        or not isinstance(source.label, str)
        or len(source.label) > 32
        or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", source.label) is None
        or not isinstance(source.url, str)
        or len(source.url) > 2048
    ):
        raise ConfigError("Invalid source configuration")
    try:
        parts = urlsplit(source.url)
        valid = (
            parts.scheme == "https"
            and bool(parts.hostname)
            and parts.username is None
            and parts.password is None
            and not parts.fragment
            and parts.port in (None, 443)
            and not any(c.isspace() or ord(c) < 32 for c in source.url)
        )
    except ValueError:
        valid = False
    if not valid:
        raise ConfigError("Invalid source configuration")
