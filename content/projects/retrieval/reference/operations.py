from dataclasses import replace
import hashlib
from .contracts import (
    Case,
    CaseResult,
    Chunk,
    Document,
    Evaluation,
    Filters,
    Hit,
    Mode,
    Principal,
    Query,
    Span,
    Key,
    integer,
)
from .support import cosine, eligible, lexical


def make_chunks(document: Document, *, width: int = 96, overlap: int = 24) -> tuple[Span, ...]:
    if type(document) is not Document:
        raise ValueError("exact document required")
    copied = replace(document)
    integer(width, 16, 512)
    integer(overlap, 0, width - 1)
    spans: list[Span] = []
    start = 0
    while start < len(copied.text):
        if len(spans) == 32:
            raise ValueError("too many windows")
        end = min(start + width, len(copied.text))
        part = copied.text[start:end]
        spans.append(
            Span(
                Key(copied.tenant, copied.id, copied.revision, len(spans)),
                start,
                end,
                part,
                hashlib.sha256(part.encode("utf-8")).hexdigest(),
            )
        )
        if end == len(copied.text):
            break
        start = end - overlap
    return tuple(spans)


def retrieve(
    chunks: tuple[Chunk, ...],
    query: Query,
    principal: Principal,
    filters: Filters = Filters(),
    *,
    k: int = 3,
    mode: Mode = "cosine",
) -> tuple[Hit, ...]:
    integer(k, 1, 10)
    if mode not in ("cosine", "lexical"):
        raise ValueError("unsupported ranking mode")
    candidates = eligible(chunks, query, principal, filters)
    qv = tuple(float(v) for v in query.values)
    scored: list[Hit] = []
    for row in candidates:
        score = cosine(row.values, qv) if mode == "cosine" else lexical(row.span.text, query.text)
        if filters.min_score is not None and score < filters.min_score:
            continue
        span = row.span
        scored.append(Hit(span.key, span.start, span.end, span.digest, score))
    scored.sort(key=lambda hit: (-hit.score, hit.key))
    return tuple(scored[:k])


def evaluate(
    chunks: tuple[Chunk, ...], cases: tuple[Case, ...], *, k: int = 3, mode: Mode = "cosine"
) -> Evaluation:
    integer(k, 1, 10)
    if mode not in ("cosine", "lexical") or type(cases) is not tuple or len(cases) > 32:
        raise ValueError("invalid bounded evaluation")
    results: list[CaseResult] = []
    seen: set[str] = set()
    for case in cases:
        if type(case) is not Case:
            raise ValueError("exact evaluation case required")
        copied = replace(case)
        if copied.id in seen:
            raise ValueError("duplicate case identity")
        seen.add(copied.id)
        candidates = eligible(chunks, copied.query, copied.principal, copied.filters)
        allowed = {row.span.key for row in candidates}
        relevant = set(copied.relevant)
        if not relevant <= allowed:
            raise ValueError("judgments name missing or ineligible chunks")
        hits = retrieve(chunks, copied.query, copied.principal, copied.filters, k=k, mode=mode)
        matched = sum(hit.key in relevant for hit in hits)
        first = next((rank for rank, hit in enumerate(hits, 1) if hit.key in relevant), None)
        recall = matched / len(relevant) if relevant else None
        reciprocal = (1 / first if first else 0.0) if relevant else None
        results.append(CaseResult(copied.id, hits, len(relevant), matched, matched / k, recall, reciprocal))
    answerable = [result for result in results if result.recall is not None]
    recall_values = [result.recall for result in results if result.recall is not None]
    reciprocal_values = [result.reciprocal_rank for result in results if result.reciprocal_rank is not None]
    return Evaluation(
        mode,
        k,
        len(results),
        len(answerable),
        len(results) - len(answerable),
        sum(result.precision_k for result in results) / len(results) if results else None,
        sum(recall_values) / len(recall_values) if recall_values else None,
        sum(reciprocal_values) / len(reciprocal_values) if reciprocal_values else None,
        sum(len(result.hits) for result in results if result.relevant == 0),
        tuple(results),
    )
