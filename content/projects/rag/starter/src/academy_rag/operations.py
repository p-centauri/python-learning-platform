from collections.abc import Callable
from academy_model_contracts import Limits, ModelConfig, Provider
from academy_retrieval import Filters, Principal, Query
from .contracts import Bundle, Policy, Record, Result
from .store import Index


def publish(index: Index, record: Record) -> bool:
    """Publish a complete newer revision/tombstone atomically; exact replay is false, conflicts fail."""
    raise NotImplementedError


def prepare(
    index: Index,
    principal: Principal,
    query: Query,
    required: tuple[str, ...],
    filters: Filters = Filters(min_score=0.6),
    policy: Policy = Policy(),
) -> Bundle:
    """Retrieve allowed candidates, apply the explicit task-term gate, rerank and pack whole evidence."""
    raise NotImplementedError


async def answer(
    index: Index,
    bundle: Bundle,
    authority: Callable[[], Principal],
    provider: Provider,
    config: ModelConfig = ModelConfig(prompt_version="rag-v1"),
    limits: Limits = Limits(max_steps=1),
) -> Result:
    """Use one bounded configured call; validate exact excerpts/citations and recheck current scope/freshness."""
    raise NotImplementedError
