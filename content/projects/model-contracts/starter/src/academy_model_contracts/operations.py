from .contracts import Limits, ModelConfig, Provider, Reply, Report, Request


def build_request(config: ModelConfig, prompt: str) -> Request:
    """Validate/copy configuration and bounded text; count complete UTF-8 fixture envelope plus output reserve."""
    raise NotImplementedError


def decode_reply(raw: object, request: Request) -> Reply:
    """Normalize strict versioned fixture bytes, usage and complete/refused/incomplete; validate completed triage only."""
    raise NotImplementedError


async def run(
    provider: Provider, config: ModelConfig, prompts: tuple[str, ...], limits: Limits = Limits()
) -> Report:
    """Preflight; reserve before each call, settle known usage, retain unknown reserves, bound attempts and total cooperative time."""
    raise NotImplementedError
