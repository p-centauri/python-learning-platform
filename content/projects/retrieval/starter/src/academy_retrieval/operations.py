from .contracts import Case, Chunk, Document, Evaluation, Filters, Hit, Mode, Principal, Query, Span


def make_chunks(document: Document, *, width: int = 96, overlap: int = 24) -> tuple[Span, ...]:
    """Bounded character windows, stable complete keys, exact offsets/digests and no repeated final suffix."""
    raise NotImplementedError


def retrieve(
    chunks: tuple[Chunk, ...],
    query: Query,
    principal: Principal,
    filters: Filters = Filters(),
    *,
    k: int = 3,
    mode: Mode = "cosine",
) -> tuple[Hit, ...]:
    """Check coherent corpus/query spec; filter latest/access/metadata before scoring; use deterministic full-key ties."""
    raise NotImplementedError


def evaluate(
    chunks: tuple[Chunk, ...], cases: tuple[Case, ...], *, k: int = 3, mode: Mode = "cosine"
) -> Evaluation:
    """Validate scoped relevance judgments, then compute exact denominators and separate no-label cases."""
    raise NotImplementedError
