from dataclasses import dataclass
import hashlib
import math
import re
from typing import Literal

Mode = Literal["cosine", "lexical"]
TOPICS = ("python", "database", "http", "policy")


def identifier(value: object) -> str:
    if type(value) is not str or re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value) is None:
        raise ValueError("invalid identifier")
    return value


def integer(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid exact integer")
    return value


def text(value: object, bound: int) -> str:
    if type(value) is not str or not value.strip() or len(value.encode("utf-8")) > bound:
        raise ValueError("invalid bounded text")
    return value


def groups(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or len(value) > 8:
        raise ValueError("invalid group set")
    for name in value:
        identifier(name)
    if len(set(value)) != len(value):
        raise ValueError("duplicate group")
    return value


@dataclass(frozen=True, slots=True)
class Spec:
    model: str = "manual-vectors"
    version: str = "fixture-v1"
    dimensions: int = 6

    def __post_init__(self) -> None:
        identifier(self.model)
        identifier(self.version)
        integer(self.dimensions, 1, 32)


def vector(values: object, dimensions: int) -> tuple[float, ...]:
    if type(values) is not tuple or len(values) != dimensions:
        raise ValueError("vector dimension mismatch")
    copied: list[float] = []
    for value in values:
        if type(value) not in (int, float) or abs(value) > 1000000 or not math.isfinite(value):
            raise ValueError("invalid finite vector coordinate")
        copied.append(float(value))
    if math.hypot(*copied) < 1e-12:
        raise ValueError("zero or too-small vector norm")
    return tuple(copied)


@dataclass(frozen=True, slots=True, order=True)
class Key:
    tenant: str
    document: str
    revision: int
    ordinal: int

    def __post_init__(self) -> None:
        identifier(self.tenant)
        identifier(self.document)
        integer(self.revision, 1, 1000000)
        integer(self.ordinal, 0, 31)


@dataclass(frozen=True, slots=True)
class Document:
    tenant: str
    id: str
    revision: int
    text: str
    topic: str = "policy"
    groups: tuple[str, ...] = ()
    active: bool = True

    def __post_init__(self) -> None:
        Key(self.tenant, self.id, self.revision, 0)
        text(self.text, 8192)
        if type(self.topic) is not str or self.topic not in TOPICS or type(self.active) is not bool:
            raise ValueError("invalid document metadata")
        groups(self.groups)


@dataclass(frozen=True, slots=True)
class Span:
    key: Key
    start: int
    end: int
    text: str
    digest: str

    def __post_init__(self) -> None:
        if type(self.key) is not Key:
            raise ValueError("exact chunk key required")
        integer(self.start, 0, 8192)
        integer(self.end, 1, 8192)
        if type(self.text) is not str or not self.text or len(self.text.encode("utf-8")) > 2048:
            raise ValueError("invalid bounded span text")
        if self.end - self.start != len(self.text):
            raise ValueError("character offsets do not match text")
        if self.digest != hashlib.sha256(self.text.encode("utf-8")).hexdigest():
            raise ValueError("chunk text digest mismatch")


@dataclass(frozen=True, slots=True)
class Chunk:
    span: Span
    spec: Spec
    values: tuple[float, ...]
    topic: str = "policy"
    groups: tuple[str, ...] = ()
    active: bool = True

    def __post_init__(self) -> None:
        if type(self.span) is not Span or type(self.spec) is not Spec:
            raise ValueError("exact chunk values required")
        vector(self.values, self.spec.dimensions)
        if type(self.topic) is not str or self.topic not in TOPICS or type(self.active) is not bool:
            raise ValueError("invalid chunk metadata")
        groups(self.groups)


@dataclass(frozen=True, slots=True)
class Principal:
    tenant: str
    groups: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        identifier(self.tenant)
        groups(self.groups)


@dataclass(frozen=True, slots=True)
class Filters:
    topic: str | None = None
    document: str | None = None
    min_score: float | None = None

    def __post_init__(self) -> None:
        if self.topic is not None and (type(self.topic) is not str or self.topic not in TOPICS):
            raise ValueError("unsupported topic filter")
        if self.document is not None:
            identifier(self.document)
        if self.min_score is not None and (
            type(self.min_score) not in (int, float)
            or not -1 <= self.min_score <= 1
            or not math.isfinite(self.min_score)
        ):
            raise ValueError("invalid similarity threshold")


@dataclass(frozen=True, slots=True)
class Query:
    spec: Spec
    text: str
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if type(self.spec) is not Spec:
            raise ValueError("exact query spec required")
        text(self.text, 512)
        vector(self.values, self.spec.dimensions)


@dataclass(frozen=True, slots=True)
class Hit:
    key: Key
    start: int
    end: int
    digest: str
    score: float


@dataclass(frozen=True, slots=True)
class Case:
    id: str
    query: Query
    principal: Principal
    filters: Filters
    relevant: tuple[Key, ...]

    def __post_init__(self) -> None:
        identifier(self.id)
        if (
            type(self.query) is not Query
            or type(self.principal) is not Principal
            or type(self.filters) is not Filters
        ):
            raise ValueError("exact case values required")
        if (
            type(self.relevant) is not tuple
            or len(self.relevant) > 16
            or any(type(k) is not Key for k in self.relevant)
            or len(set(self.relevant)) != len(self.relevant)
        ):
            raise ValueError("invalid relevance keys")


@dataclass(frozen=True, slots=True)
class CaseResult:
    id: str
    hits: tuple[Hit, ...]
    relevant: int
    matched: int
    precision_k: float
    recall: float | None
    reciprocal_rank: float | None


@dataclass(frozen=True, slots=True)
class Evaluation:
    mode: Mode
    k: int
    cases: int
    answerable: int
    no_labels: int
    precision_all: float | None
    recall_answerable: float | None
    mrr_answerable: float | None
    unwanted_returns: int
    results: tuple[CaseResult, ...]


@dataclass(frozen=True, slots=True)
class Dataset:
    version: str
    spec: Spec
    chunks: tuple[Chunk, ...]
    cases: tuple[Case, ...]
