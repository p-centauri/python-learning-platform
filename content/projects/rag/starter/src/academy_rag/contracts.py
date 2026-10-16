from dataclasses import dataclass
from typing import Literal
from academy_model_contracts import Usage
from academy_retrieval import Document, Filters, Principal, Query, Span
from academy_retrieval.contracts import Key, identifier, integer

Reason = Literal[
    "answered",
    "missing_evidence",
    "stale_evidence",
    "principal_changed",
    "invalid_output",
    "refused",
    "incomplete",
    "timeout",
    "provider_error",
    "cost_limit",
    "context_limit",
]


@dataclass(frozen=True, slots=True)
class Record:
    tenant: str
    id: str
    revision: int
    document: Document | None
    vectors: tuple[tuple[float, ...], ...] = ()

    def __post_init__(self) -> None:
        Key(self.tenant, self.id, self.revision, 0)
        if type(self.vectors) is not tuple or len(self.vectors) > 32:
            raise ValueError("invalid vector batch")
        if self.document is None:
            if self.vectors:
                raise ValueError("tombstone has no vectors")
        elif type(self.document) is not Document or (
            self.document.tenant,
            self.document.id,
            self.document.revision,
        ) != (self.tenant, self.id, self.revision):
            raise ValueError("document identity mismatch")


@dataclass(frozen=True, slots=True)
class Policy:
    candidates: int = 6
    passages: int = 3
    context_bytes: int = 2048

    def __post_init__(self) -> None:
        integer(self.candidates, 1, 10)
        integer(self.passages, 1, 3)
        integer(self.context_bytes, 16, 4096)
        if self.passages > self.candidates:
            raise ValueError("passage count exceeds candidates")


@dataclass(frozen=True, slots=True)
class Evidence:
    id: str
    span: Span
    similarity: float
    lexical: float


@dataclass(frozen=True, slots=True)
class Bundle:
    epoch: int
    principal: Principal
    query: Query
    filters: Filters
    required: tuple[str, ...]
    policy: Policy
    evidence: tuple[Evidence, ...]
    omitted: int


@dataclass(frozen=True, slots=True)
class Citation:
    id: str
    span: Span

    def __post_init__(self) -> None:
        identifier(self.id)
        if type(self.span) is not Span:
            raise ValueError("exact citation span required")


@dataclass(frozen=True, slots=True)
class Result:
    reason: Reason
    text: str | None
    citations: tuple[Citation, ...]
    attempts: int
    charged: int
    usage: Usage | None
    epoch: int
    model: str
    prompt_version: str
    schema: str = "rag-quotes-v1"
