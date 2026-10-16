from dataclasses import dataclass, field
from enum import Enum
from threading import Event
from fastapi import FastAPI


class ConfigurationError(ValueError):
    def __init__(self) -> None:
        super().__init__("invalid release configuration")


class Reason(str, Enum):
    READY = "ready"
    SCHEMA_HEAD = "schema-head"
    SCHEMA_CONTRACT = "schema-contract"
    STORAGE_UNAVAILABLE = "storage-unavailable"
    STOPPING = "stopping"


@dataclass(frozen=True, slots=True)
class Settings:
    dsn: str = field(repr=False)
    tokens: tuple[tuple[str, str], ...] = field(repr=False)


@dataclass(frozen=True, slots=True)
class Readiness:
    reason: Reason

    @property
    def ready(self) -> bool:
        return self.reason is Reason.READY


class StartupRefused(RuntimeError):
    def __init__(self, reason: Reason) -> None:
        self.reason = reason
        super().__init__("release startup refused: " + reason.value)


@dataclass(frozen=True, slots=True)
class Release:
    app: FastAPI = field(repr=False)
    stop: Event = field(repr=False)
