import json
import pytest
from academy_model_contracts import ModelConfig
from academy_tools import decode_proposal
from academy_tools.fixtures import setup, wire
from academy_tools.support import canonical, request


@pytest.mark.parametrize("kind", ["read", "write", "finish", "refused", "incomplete"])
def test_exact_variants(tmp_path, kind):
    _, _, ctx, _ = setup(tmp_path)
    sent = request(ctx, ModelConfig(), ())
    value = wire(kind)
    if kind in ("refused", "incomplete"):
        value.update(status=kind, proposal=None)
    result = decode_proposal(canonical(value), sent)
    assert result.kind == {"read": "call", "write": "call"}.get(kind, kind)
    assert result.usage.input_units == 3 and result.usage.output_units == 4


@pytest.mark.parametrize(
    "mutation",
    [
        "root-extra",
        "missing",
        "wrong-model",
        "wrong-schema",
        "bad-status",
        "tool",
        "args-extra",
        "args-missing",
        "url",
        "bool-id",
        "bool-usage",
        "negative-usage",
        "huge-usage",
        "high-output",
        "float-usage",
        "blank-label",
        "long-label",
        "control-label",
        "refused-call",
        "finish-extra",
    ],
)
def test_rejects_untrusted_envelopes(tmp_path, mutation):
    _, _, ctx, _ = setup(tmp_path)
    sent = request(ctx, ModelConfig(), ())
    v = wire()
    if mutation == "root-extra":
        v["role"] = "admin"
    if mutation == "missing":
        del v["model"]
    if mutation == "wrong-model":
        v["model"] = "other-model"
    if mutation == "wrong-schema":
        v["schema"] = "rag-quotes-v1"
    if mutation == "bad-status":
        v["status"] = "partial"
    if mutation == "tool":
        v["proposal"]["name"] = "run_shell"
    if mutation == "args-extra":
        v["proposal"]["arguments"]["tenant"] = "foreign"
    if mutation == "args-missing":
        del v["proposal"]["arguments"]["citation"]
    if mutation == "url":
        v["proposal"]["arguments"]["citation"] = "https://example.com"
    if mutation == "bool-id":
        v["proposal"]["id"] = True
    if mutation == "bool-usage":
        v["usage"]["input_units"] = True
    if mutation == "negative-usage":
        v["usage"]["input_units"] = -1
    if mutation == "huge-usage":
        v["usage"]["input_units"] = 10**1000
    if mutation == "high-output":
        v["usage"]["output_units"] = sent.config.output_units + 1
    if mutation == "float-usage":
        v["usage"]["output_units"] = 4.0
    if mutation == "blank-label":
        v["proposal"]["arguments"]["label"] = "  "
    if mutation == "long-label":
        v["proposal"]["arguments"]["label"] = "é" * 61
    if mutation == "control-label":
        v["proposal"]["arguments"]["label"] = "a\nb"
    if mutation == "refused-call":
        v["status"] = "refused"
    if mutation == "finish-extra":
        v["proposal"] = {"kind": "finish", "summary": "I saved everything"}
    with pytest.raises(ValueError):
        decode_proposal(canonical(v), sent)


@pytest.mark.parametrize(
    "raw",
    [b"", b"x" * 16385, b"\xff", b'{"x":1,"x":2}', b'{"x":NaN}', b"[]", "{}", b"null"],
    ids=["empty", "large", "utf8", "duplicate", "nonfinite", "array", "str", "null"],
)
def test_exact_bounded_json(tmp_path, raw):
    _, _, ctx, _ = setup(tmp_path)
    with pytest.raises((ValueError, UnicodeError)):
        decode_proposal(raw, request(ctx, ModelConfig(), ()))


def test_request_owns_complete_byte_reservation_and_labels_untrusted_input(tmp_path):
    _, _, ctx, _ = setup(tmp_path)
    c = ModelConfig(prompt_version="tools-v1", input_rate=7, output_rate=11)
    sent = request(ctx, c, ())
    v = json.loads(sent.body)
    assert sent.input_bound == len(sent.body)
    assert sent.reserve == len(sent.body) * 7 + c.output_units * 11
    assert v["input"]["untrusted_task"] == ctx.task and set(v["input"]["tools"]) == {
        "source_excerpt",
        "save_note",
    }
    assert "actor" not in v["input"] and "approval" not in v["input"]
