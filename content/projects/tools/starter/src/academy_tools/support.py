import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import asdict
import hashlib
import json
from typing import cast
from academy_model_contracts import ModelConfig, Request
from academy_rag import Index, resolve
from .contracts import Authority, Call, Context, Outcome
from .store import Store


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def nonfinite(value: str) -> object:
    raise ValueError("non-finite JSON")


def parse(raw: object) -> object:
    if type(raw) is not bytes or not 1 <= len(raw) <= 16384:
        raise ValueError("bounded exact response bytes required")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)


def fields(value: object, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError("exact JSON fields required")
    return cast(dict[str, object], value)


def current(context: Context, index: Index, authority: Callable[[], Authority]) -> Authority:
    granted = authority()
    if (
        type(granted) is not Authority
        or granted.actor != context.actor
        or granted.principal != context.principal
        or not granted.read
    ):
        raise ValueError("forbidden")
    if any(resolve(index, c, granted.principal) is None for c in context.citations):
        raise ValueError("stale_source")
    return granted


def approval_for(context: Context, call: Call) -> str:
    if call.name != "save_note":
        raise ValueError("write action required")
    citation = next((c for c in context.citations if c.id == call.citation), None)
    if citation is None:
        raise ValueError("unknown citation")
    # Model call IDs are intentionally excluded: the application owns retry identity.
    value = {
        "policy": "local-note-v1",
        "tenant": context.principal.tenant,
        "actor": context.actor,
        "operation": context.operation_id,
        "tool": call.name,
        "label": call.label,
        "citation": asdict(citation),
    }
    return hashlib.sha256(canonical(value)).hexdigest()


def request(context: Context, config: ModelConfig, history: tuple[Outcome, ...]) -> Request:
    payload = {
        "schema": "tool-proposals-v1",
        "tools": {
            "source_excerpt": {"citation": "selected ID only"},
            "save_note": {
                "citation": "selected ID only",
                "label": "1..120 UTF-8 bytes; application approval required",
            },
        },
        "untrusted_task": context.task,
        "selected_ids": [c.id for c in context.citations],
        "observed_tool_results": [asdict(o) for o in history],
    }
    body = canonical(
        {
            "provider": config.provider_id,
            "dialect": config.dialect,
            "model": config.model,
            "prompt_version": config.prompt_version,
            "input": payload,
            "max_output_units": config.output_units,
        }
    )
    size = len(body)
    return Request(config, body, size, size * config.input_rate + config.output_units * config.output_rate)


class LocalTools:
    """Borrowed local resources; hooks are trusted controlled fixtures, never model data."""

    def __init__(
        self,
        index: Index,
        store: Store,
        authority: Callable[[], Authority],
        before: Callable[[], Awaitable[None]] | None = None,
        after: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self.index = index
        self.store = store
        self.authority = authority
        self.before = before
        self.after = after

    async def invoke(self, context: Context, call: Call) -> Outcome:
        from .operations import execute

        if self.before is not None:
            await self.before()
        await asyncio.sleep(0)
        outcome = execute(context, call, self.index, self.store, self.authority)
        if self.after is not None:
            await self.after()
        return outcome
