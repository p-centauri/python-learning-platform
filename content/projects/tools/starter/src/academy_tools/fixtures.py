import asyncio
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any
from academy_model_contracts import Adapter
from academy_rag import Citation, Index, publish
from academy_rag.fixtures import SPEC, record
from academy_retrieval import Principal, make_chunks
from .contracts import Authority, Call, Context
from .store import Store
from .support import approval_for, canonical

FIXTURE = "tools-fixture-v1"


def setup(directory: Path) -> tuple[Index, Store, Context, Authority]:
    index = Index(directory / "sources.sqlite", SPEC)
    index.initialize()
    doc = record()
    publish(index, doc)
    assert doc.document is not None
    citation = Citation("e0", make_chunks(doc.document)[0])
    context = Context(Principal("alpha", ("ops",)), "learner", "note-operation-1", (citation,))
    call = Call("write-1", "save_note", "e0", "Review file cleanup")
    granted = Authority(context.principal, context.actor, True, approval_for(context, call))
    store = Store(directory / "tools.sqlite")
    store.initialize()
    return index, store, context, granted


def wire(kind: str = "write", call_id: str = "write-1", title: str = "Review file cleanup") -> dict[str, Any]:
    proposal: object = {
        "kind": "call",
        "id": call_id,
        "name": "save_note",
        "arguments": {"citation": "e0", "label": title},
    }
    if kind == "read":
        proposal = {"kind": "call", "id": call_id, "name": "source_excerpt", "arguments": {"citation": "e0"}}
    if kind == "finish":
        proposal = {"kind": "finish"}
    return {
        "model": "fixture-model-2026-10",
        "schema": "tool-proposals-v1",
        "status": "complete",
        "proposal": proposal,
        "usage": {"input_units": 3, "output_units": 4},
    }


class ScriptedTransport:
    def __init__(
        self,
        sequence: tuple[str, ...] = ("read", "write", "finish"),
        change: Callable[[], None] | None = None,
    ) -> None:
        self.sequence = sequence
        self.change = change
        self.requests: list[bytes] = []
        self.entered = asyncio.Event()
        self.cleaned = False

    async def send(self, body: bytes) -> object:
        number = len(self.requests)
        self.requests.append(body)
        mode = self.sequence[min(number, len(self.sequence) - 1)]
        if self.change is not None:
            self.change()
        if mode == "wait":
            self.entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0)
                self.cleaned = True
        if mode == "error":
            raise OSError("controlled-private-error")
        value = wire(mode, f"call-{number}")
        if mode == "new-id":
            value = wire("write", "different-model-id")
        if mode == "changed":
            value = wire("write", "changed-id", "Unapproved changed label")
        if mode in ("refused", "incomplete"):
            value.update(status=mode, proposal=None)
        if mode == "unknown":
            value["proposal"]["name"] = "fetch_url"
        if mode == "extra":
            value["proposal"]["arguments"]["tenant"] = "foreign"
        if mode == "bad-usage":
            value["usage"]["input_units"] = True
        return canonical(value)

    def provider(self) -> Adapter:
        return Adapter("fixture-a", "message-v1", self)


def revoked(granted: Authority) -> Authority:
    return replace(granted, read=False, approval=None)
