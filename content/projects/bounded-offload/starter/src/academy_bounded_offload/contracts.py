"""Supplied immutable job descriptions; paths remain caller-owned resources."""
from dataclasses import dataclass
from pathlib import Path
import re

def bounded_integer(value: int, low: int, high: int, name: str) -> None:
    if type(value) is not int:
        raise TypeError("Expected exact integer " + name)
    if not low <= value <= high:
        raise ValueError("Invalid " + name)

def validate_settings(pending: int, limit: int) -> None:
    bounded_integer(pending, 1, 4, "pending")
    bounded_integer(limit, 0, 16, "limit")

@dataclass(frozen=True)
class Job:
    id: str
    path: str

    def __post_init__(self) -> None:
        if type(self.id) is not str or type(self.path) is not str:
            raise TypeError("Expected exact text fields")
        if not 1 <= len(self.id) <= 32 or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", self.id) is None:
            raise ValueError("Invalid job id")
        if not 1 <= len(self.path) <= 512 or not Path(self.path).is_absolute():
            raise ValueError("Expected bounded absolute path")

@dataclass(frozen=True)
class Outcome:
    id: str
    value: int
    worker_pid: int
    worker_thread: str
    file_closed: bool
