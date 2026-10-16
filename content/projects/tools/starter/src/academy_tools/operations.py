from collections.abc import Callable
from academy_model_contracts import Limits, ModelConfig, Provider, Request
from academy_rag import Index
from .contracts import Authority, Call, Context, Outcome, Proposal, Report, Toolbox
from .store import Store


def decode_proposal(raw: object, sent: Request) -> Proposal:
    """Validate exact bounded JSON variants and metering without granting authority."""
    raise NotImplementedError


def execute(
    context: Context, call: Call, index: Index, store: Store, authority: Callable[[], Authority]
) -> Outcome:
    """Refresh authority/source, bind approval and atomically apply or replay the local note."""
    raise NotImplementedError


async def run(
    context: Context,
    index: Index,
    store: Store,
    authority: Callable[[], Authority],
    provider: Provider,
    tools: Toolbox | None = None,
    config: ModelConfig = ModelConfig(prompt_version="tools-v1"),
    limits: Limits = Limits(),
) -> Report:
    """Bound the whole proposal/tool loop, preserve uncertainty and propagate cancellation."""
    raise NotImplementedError
