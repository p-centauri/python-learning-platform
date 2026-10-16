import asyncio
from .contracts import Dialect
from .support import encode


class ScriptedTransport:
    """Trusted local finite responses; no model runs and no remote request is made."""

    def __init__(self, responses: tuple[object, ...]) -> None:
        if type(responses) is not tuple or len(responses) > 8:
            raise ValueError("invalid fixture script")
        self.responses = responses
        self.requests: list[bytes] = []

    async def send(self, body: bytes) -> object:
        index = len(self.requests)
        self.requests.append(body)
        await asyncio.sleep(0)
        if index >= len(self.responses):
            raise RuntimeError("fixture script exhausted")
        response = self.responses[index]
        if isinstance(response, Exception):
            raise response
        return response


class WaitingTransport:
    """Cooperative pending fixture; entered/finished flags observe awaited cancellation cleanup."""

    def __init__(self) -> None:
        self.entered = asyncio.Event()
        self.finished = asyncio.Event()
        self.requests: list[bytes] = []

    async def send(self, body: bytes) -> object:
        self.requests.append(body)
        self.entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            self.finished.set()
        raise AssertionError("unreachable waiting fixture")


def response(
    dialect: Dialect = "message-v1",
    *,
    kind: str = "complete",
    model: str = "fixture-model-2026-10",
    input_units: int = 10,
    output_units: int = 20,
    text: str | None = None,
) -> bytes:
    if text is None:
        text = encode(dict(queue="python", summary="Check the traceback", needs_human=True)).decode()
    if dialect == "message-v1":
        return encode(
            dict(
                model=model,
                status=kind,
                text=text if kind != "refused" else None,
                refusal="fixture refusal" if kind == "refused" else None,
                usage=dict(input=input_units, output=output_units),
            )
        )
    field = {"complete": "content", "refused": "refusal", "incomplete": "partial"}[kind]
    stop = {"complete": "done", "refused": "refused", "incomplete": "limit"}[kind]
    return encode(
        dict(
            model_id=model,
            stop=stop,
            result={field: text},
            meter=dict(input=input_units, output=output_units),
        )
    )
