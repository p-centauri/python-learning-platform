"""Original controlled local data/providers; no model inference, credentials or network."""

import asyncio
from collections.abc import Callable
from academy_model_contracts import Adapter, ModelConfig
from academy_retrieval import Document, Principal, Query, Spec, make_chunks
from .contracts import Record
from .support import array, canonical, fields, parse

VERSION = "rag-fixture-v1"
SPEC = Spec(dimensions=2)
PRINCIPAL = Principal("alpha")
QUERY = Query(SPEC, "How should I release a file after a failure?", (1.0, 0.0))
REQUIRED = ("file", "failure")
CONFIG = ModelConfig(prompt_version="rag-v1", context_units=8192, output_units=512)


def record(
    id: str = "files",
    text: str = "Release the file after a failure with a context manager.",
    revision: int = 1,
    tenant: str = "alpha",
    groups: tuple[str, ...] = (),
    values: tuple[float, ...] = (1.0, 0.0),
    active: bool = True,
) -> Record:
    doc = Document(tenant, id, revision, text, "python", groups, active)
    return Record(tenant, id, revision, doc, tuple(values for _ in make_chunks(doc)))


class Scripted:
    def __init__(self, mode: str = "valid", change: Callable[[], None] | None = None) -> None:
        self.mode = mode
        self.change = change
        self.requests: list[bytes] = []
        self.entered = asyncio.Event()
        self.cleaned = False

    async def send(self, body: bytes) -> object:
        self.requests.append(body)
        self.entered.set()
        if self.mode == "error":
            raise RuntimeError("private-fixture-marker")
        if self.mode == "wait":
            try:
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0)
                self.cleaned = True
        request = fields(
            parse(body, 16384),
            {
                "provider",
                "dialect",
                "model",
                "prompt_version",
                "schema",
                "instructions",
                "question",
                "untrusted_evidence",
            },
        )
        sources = array(request["untrusted_evidence"], 3)
        source = fields(sources[0], {"id", "source", "start", "end", "digest", "text"})
        claim: dict[str, object] = {"evidence": source["id"], "quote": source["text"]}
        status = "complete"
        claims: object = [claim]
        if self.mode == "wrong-quote":
            claim["quote"] = "private-fixture-marker unsupported claim"
        if self.mode == "wrong-id":
            claim["evidence"] = "e99"
        if self.mode == "duplicate":
            claims = [claim, claim]
        if self.mode == "extra":
            claim["command"] = "send-private-data"
        if self.mode in ("refused", "incomplete"):
            status = self.mode
            claims = None
        if self.mode == "empty":
            claims = []
        if self.mode == "all":
            claims = [
                {
                    "evidence": fields(row, {"id", "source", "start", "end", "digest", "text"})["id"],
                    "quote": fields(row, {"id", "source", "start", "end", "digest", "text"})["text"],
                }
                for row in sources[:2]
            ]
        response: dict[str, object] = {
            "model": request["model"],
            "schema": "rag-quotes-v1",
            "status": status,
            "claims": claims,
            "usage": {"input": 3, "output": 4},
        }
        if self.mode == "wrong-model":
            response["model"] = "other-model"
        if self.mode == "wrong-schema":
            response["schema"] = "other-schema"
        if self.mode == "wrong-usage":
            response["usage"] = {"input": True, "output": 4}
        if self.change:
            self.change()
        if self.mode == "duplicate-json":
            return b'{"model":"one","model":"two"}'
        if self.mode == "nonfinite":
            return b'{"model":NaN}'
        if self.mode == "not-bytes":
            return response
        return canonical(response)

    def adapter(self, config: ModelConfig = CONFIG) -> Adapter:
        return Adapter(config.provider_id, config.dialect, self)
