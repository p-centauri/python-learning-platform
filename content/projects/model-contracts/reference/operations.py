import asyncio
from dataclasses import replace
from .contracts import (
    Decision,
    Kind,
    Limits,
    ModelConfig,
    Provider,
    Reply,
    Report,
    Request,
    Step,
    Stop,
    Usage,
    integer,
)
from .support import parse, wire


def build_request(config: ModelConfig, prompt: str) -> Request:
    if (
        type(config) is not ModelConfig
        or type(prompt) is not str
        or not prompt.strip()
        or len(prompt.encode("utf-8")) > 4096
    ):
        raise ValueError("invalid configured request")
    copied = replace(config)
    body = wire(copied, prompt)
    # A complete-byte fixture counter; deliberately NOT a real tokenizer.
    units = len(body)
    if units + copied.output_units > copied.context_units:
        raise ValueError("fixture context capacity exceeded")
    reserve = units * copied.input_rate + copied.output_units * copied.output_rate
    return Request(copied, body, units, reserve)


def decode_reply(raw: object, request: Request) -> Reply:
    if type(raw) is not bytes:
        raise ValueError("response must be bytes")
    payload = parse(raw, 16384)
    if type(payload) is not dict:
        raise ValueError("invalid fixture envelope")
    kind: Kind
    text: object
    if request.config.dialect == "message-v1":
        if (
            set(payload) != {"model", "status", "text", "refusal", "usage"}
            or payload["model"] != request.config.model
        ):
            raise ValueError("fixture identity or shape mismatch")
        status = payload["status"]
        if status == "complete":
            kind = "complete"
            if payload["refusal"] is not None:
                raise ValueError("mixed completion and refusal")
            text = payload["text"]
        elif status == "refused":
            kind = "refused"
            if payload["text"] is not None:
                raise ValueError("mixed refusal and content")
            text = payload["refusal"]
        elif status == "incomplete":
            kind = "incomplete"
            if payload["refusal"] is not None:
                raise ValueError("mixed incomplete and refusal")
            text = payload["text"]
        else:
            raise ValueError("unknown fixture status")
        metering = payload["usage"]
    else:
        if (
            set(payload) != {"model_id", "stop", "result", "meter"}
            or payload["model_id"] != request.config.model
        ):
            raise ValueError("fixture identity or shape mismatch")
        status = payload["stop"]
        mapping: dict[str, tuple[Kind, str]] = {
            "done": ("complete", "content"),
            "refused": ("refused", "refusal"),
            "limit": ("incomplete", "partial"),
        }
        if type(status) is not str or status not in mapping:
            raise ValueError("unknown fixture stop")
        kind, field = mapping[status]
        result = payload["result"]
        if type(result) is not dict or set(result) != {field}:
            raise ValueError("mixed fixture result")
        text = result[field]
        metering = payload["meter"]
    if type(metering) is not dict or set(metering) != {"input", "output"}:
        raise ValueError("unknown fixture usage")
    usage = Usage(
        integer(metering["input"], 0, request.input_bound),
        integer(metering["output"], 0, request.config.output_units),
    )
    if kind == "incomplete" and text is None:
        return Reply(kind, usage, None)
    if type(text) is not str or not text.strip() or len(text.encode("utf-8")) > 4096:
        raise ValueError("invalid bounded fixture text")
    if kind != "complete":
        # Never parse refusal/partial text into an actionable result or expose its raw reason.
        return Reply(kind, usage, None)
    decoded = parse(text.encode("utf-8"), 4096)
    if type(decoded) is not dict or set(decoded) != {"queue", "summary", "needs_human"}:
        raise ValueError("invalid triage proposal")
    decision = Decision(decoded["queue"], decoded["summary"], decoded["needs_human"])
    return Reply(kind, usage, decision)


async def run(
    provider: Provider, config: ModelConfig, prompts: tuple[str, ...], limits: Limits = Limits()
) -> Report:
    if (
        type(config) is not ModelConfig
        or type(limits) is not Limits
        or type(prompts) is not tuple
        or len(prompts) > 8
    ):
        raise ValueError("invalid bounded run")
    copied = replace(config)
    policy = replace(limits)
    if provider.provider_id != copied.provider_id or provider.dialect != copied.dialect:
        raise ValueError("provider configuration mismatch")
    requests = tuple(build_request(copied, prompt) for prompt in prompts)
    steps: list[Step] = []
    charged = 0
    stopped: Stop = "finished"
    loop = asyncio.get_running_loop()
    deadline = loop.time() + policy.timeout_ms / 1000
    for index, request in enumerate(requests):
        if len(steps) == policy.max_steps:
            stopped = "step_limit"
            break
        if charged + request.reserve > policy.max_cost:
            stopped = "cost_limit"
            break
        remaining = deadline - loop.time()
        if remaining <= 0:
            stopped = "deadline"
            break
        charged += request.reserve
        try:
            async with asyncio.timeout(remaining):
                raw = await provider.complete(request)
        except TimeoutError:
            steps.append(Step(index, "timeout", request.reserve, request.reserve, None, None))
            stopped = "timeout"
            break
        except Exception:
            steps.append(Step(index, "provider_error", request.reserve, request.reserve, None, None))
            stopped = "provider_error"
            break
        try:
            reply = decode_reply(raw, request)
        except (ValueError, TypeError, RecursionError):
            steps.append(Step(index, "invalid_response", request.reserve, request.reserve, None, None))
            stopped = "invalid_response"
            break
        actual = reply.usage.input_units * copied.input_rate + reply.usage.output_units * copied.output_rate
        charged += actual - request.reserve
        steps.append(Step(index, reply.kind, request.reserve, actual, reply.usage, reply.decision))
        if reply.kind != "complete":
            stopped = reply.kind
            break
    return Report(
        copied.provider_id,
        copied.model,
        copied.prompt_version,
        "triage-schema-v1",
        stopped,
        charged,
        tuple(steps),
    )
