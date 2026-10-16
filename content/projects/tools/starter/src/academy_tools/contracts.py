from dataclasses import dataclass
import re
from typing import Literal, Protocol
from academy_model_contracts import Usage
from academy_model_contracts.contracts import identifier, integer
from academy_rag import Citation
from academy_retrieval import Principal

ToolName = Literal["source_excerpt", "save_note"]


def label(value: object) -> str:
    if type(value) is not str or not value.strip() or len(value.encode("utf-8")) > 120:
        raise ValueError("invalid note label")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("control character in label")
    return value


@dataclass(frozen=True, slots=True)
class Call:
    id: str
    name: ToolName
    citation: str
    label: str | None = None

    def __post_init__(self) -> None:
        identifier(self.id)
        identifier(self.citation)
        if self.name not in ("source_excerpt", "save_note"):
            raise ValueError("tool not allowlisted")
        if self.name == "source_excerpt" and self.label is not None:
            raise ValueError("read has no label")
        if self.name == "save_note":
            label(self.label)


@dataclass(frozen=True, slots=True)
class Context:
    principal: Principal
    actor: str
    operation_id: str
    citations: tuple[Citation, ...]
    task: str = "Read the source and save the approved note."
    max_notes: int = 4

    def __post_init__(self) -> None:
        if type(self.principal) is not Principal:
            raise ValueError("application principal required")
        identifier(self.actor)
        identifier(self.operation_id)
        if type(self.citations) is not tuple or not 1 <= len(self.citations) <= 3:
            raise ValueError("bounded exact citations required")
        if any(type(c) is not Citation for c in self.citations):
            raise ValueError("exact citation required")
        if len({c.id for c in self.citations}) != len(self.citations):
            raise ValueError("duplicate evidence id")
        if any(c.span.key.tenant != self.principal.tenant for c in self.citations):
            raise ValueError("cross-tenant citation")
        if type(self.task) is not str or not self.task.strip() or len(self.task.encode("utf-8")) > 512:
            raise ValueError("bounded untrusted task required")
        integer(self.max_notes, 1, 8)


@dataclass(frozen=True, slots=True)
class Authority:
    principal: Principal
    actor: str
    read: bool = True
    approval: str | None = None

    def __post_init__(self) -> None:
        if type(self.principal) is not Principal or type(self.read) is not bool:
            raise ValueError("exact application authority required")
        identifier(self.actor)
        if self.approval is not None and (
            type(self.approval) is not str or re.fullmatch(r"[a-f0-9]{64}", self.approval) is None
        ):
            raise ValueError("invalid application approval")


@dataclass(frozen=True, slots=True)
class Proposal:
    kind: Literal["call", "finish", "refused", "incomplete"]
    call: Call | None
    usage: Usage


@dataclass(frozen=True, slots=True)
class Outcome:
    reason: str
    call_id: str
    note_id: int | None = None
    text: str | None = None
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class Step:
    index: int
    kind: str
    charged: int
    usage: Usage | None
    outcome: Outcome | None = None


@dataclass(frozen=True, slots=True)
class Report:
    stopped: str
    charged: int
    attempts: int
    steps: tuple[Step, ...]
    provider_id: str
    model: str
    prompt_version: str
    schema: str = "tool-proposals-v1"


class Toolbox(Protocol):
    async def invoke(self, context: Context, call: Call) -> Outcome: ...
