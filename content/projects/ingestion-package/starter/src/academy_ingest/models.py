from dataclasses import dataclass

MAX_LINE_BYTES = 1024
MAX_BODY_BYTES = 8192


@dataclass(frozen=True)
class Record:
    id: str
    value: int


class RecordError(ValueError):
    """Malformed input at a one-based physical line."""


class FeedError(ValueError):
    """Invalid source, status, media type, size or HTTP transport failure."""
