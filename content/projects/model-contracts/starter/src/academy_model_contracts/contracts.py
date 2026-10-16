from dataclasses import dataclass
import re
from typing import Literal, Protocol

Dialect = Literal["message-v1", "completion-v1"]
Kind = Literal["complete", "refused", "incomplete"]
StepKind = Literal["complete", "refused", "incomplete", "timeout", "provider_error", "invalid_response"]
Stop = Literal[
    "finished",
    "step_limit",
    "cost_limit",
    "deadline",
    "refused",
    "incomplete",
    "timeout",
    "provider_error",
    "invalid_response",
]


def identifier(value: object) -> str:
    if type(value) is not str or re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value) is None:
        raise ValueError("invalid configured identifier")
    return value


def integer(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid exact integer")
    return value


@dataclass(frozen=True, slots=True)
class ModelConfig:
    provider_id: str = "fixture-a"
    dialect: Dialect = "message-v1"
    model: str = "fixture-model-2026-10"
    prompt_version: str = "triage-v1"
    context_units: int = 8192
    output_units: int = 256
    input_rate: int = 2
    output_rate: int = 5

    def __post_init__(self) -> None:
        for name in (self.provider_id, self.model, self.prompt_version):
            identifier(name)
        if self.dialect not in ("message-v1", "completion-v1"):
            raise ValueError("unsupported configured dialect")
        integer(self.context_units, 1, 16384)
        integer(self.output_units, 1, 1024)
        integer(self.input_rate, 0, 1000)
        integer(self.output_rate, 0, 1000)


@dataclass(frozen=True, slots=True)
class Request:
    config: ModelConfig
    body: bytes
    input_bound: int
    reserve: int


@dataclass(frozen=True, slots=True)
class Usage:
    input_units: int
    output_units: int


@dataclass(frozen=True, slots=True)
class Decision:
    queue: str
    summary: str
    needs_human: bool

    def __post_init__(self) -> None:
        if type(self.queue) is not str or self.queue not in ("python", "database", "http"):
            raise ValueError("unsupported queue")
        if (
            type(self.summary) is not str
            or not self.summary.strip()
            or len(self.summary.encode("utf-8")) > 240
        ):
            raise ValueError("invalid bounded summary")
        if type(self.needs_human) is not bool:
            raise ValueError("exact human-review flag required")


@dataclass(frozen=True, slots=True)
class Reply:
    kind: Kind
    usage: Usage
    decision: Decision | None


@dataclass(frozen=True, slots=True)
class Limits:
    max_steps: int = 3
    max_cost: int = 10000
    timeout_ms: int = 1000

    def __post_init__(self) -> None:
        integer(self.max_steps, 1, 8)
        integer(self.max_cost, 0, 100000000)
        integer(self.timeout_ms, 1, 10000)


@dataclass(frozen=True, slots=True)
class Step:
    index: int
    kind: StepKind
    reserved: int
    charged: int
    usage: Usage | None
    decision: Decision | None


@dataclass(frozen=True, slots=True)
class Report:
    provider_id: str
    model: str
    prompt_version: str
    schema_version: str
    stopped: Stop
    charged: int
    steps: tuple[Step, ...]


class Provider(Protocol):
    @property
    def provider_id(self) -> str: ...
    @property
    def dialect(self) -> Dialect: ...
    async def complete(self, request: Request) -> object: ...


class Transport(Protocol):
    async def send(self, body: bytes) -> object: ...
