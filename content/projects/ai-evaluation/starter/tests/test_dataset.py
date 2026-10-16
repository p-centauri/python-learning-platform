from dataclasses import replace
from importlib.resources import files
import json
import pytest
from academy_ai_evaluation import Policy, load_suite, suite_digest


def resource():
    return json.loads(files("academy_ai_evaluation").joinpath("release-cases.json").read_text())


def test_fixed_packaged_version_digest_and_critical_coverage():
    s = load_suite()
    assert len(s.cases) == 18 and s.purpose == "development-controlled"
    assert {c.layer for c in s.cases} == {"retrieval", "rag", "tools"}
    assert Policy().dataset_digest == suite_digest(s)
    assert [c.id for c in s.cases if c.human] == ["rag-public", "rag-malicious-source"]


@pytest.mark.parametrize(
    "change",
    [
        "version",
        "purpose",
        "extra",
        "case-extra",
        "missing",
        "duplicate",
        "scenario",
        "layer",
        "bool-effect",
        "missing-human",
        "labels-type",
        "label-key",
    ],
)
def test_strict_dataset_cases(change):
    v = resource()
    if change == "version":
        v["version"] = "next-v2"
    if change == "purpose":
        v["purpose"] = "held-out"
    if change == "extra":
        v["approved"] = True
    if change == "case-extra":
        v["cases"][0]["role"] = "admin"
    if change == "missing":
        v["cases"].pop()
    if change == "duplicate":
        v["cases"][-1] = v["cases"][0]
    if change == "scenario":
        v["cases"][0]["scenario"] = "unknown"
    if change == "layer":
        v["cases"][0]["layer"] = "tools"
    if change == "bool-effect":
        v["cases"][0]["effects"] = True
    if change == "missing-human":
        v["cases"][4]["human"] = False
    if change == "labels-type":
        v["cases"][0]["relevant"] = "files"
    if change == "label-key":
        v["cases"][0]["relevant"] = ["files"]
    with pytest.raises(ValueError):
        load_suite(json.dumps(v).encode())


@pytest.mark.parametrize(
    "raw",
    [b"", b"x" * 32769, b"\xff", b'{"version":1,"version":2}', b'{"value":NaN}', b"[]"],
    ids=["empty", "large", "utf8", "duplicate", "nonfinite", "array"],
)
def test_strict_resource_bytes(raw):
    with pytest.raises((ValueError, UnicodeError)):
        load_suite(raw)


def test_dataset_fingerprint_changes_with_a_new_label():
    s = load_suite()
    rows = list(s.cases)
    rows[0] = replace(rows[0], relevant=("alpha:other:1:0",))
    assert suite_digest(replace(s, cases=tuple(rows))) != suite_digest(s)
