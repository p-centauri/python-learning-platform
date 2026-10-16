from importlib.resources import files
import json
import pytest
from academy_retrieval import evaluate
from academy_retrieval.dataset import decode_fixture, load_fixture


def test_installed_fixture_is_original_finite_and_deterministic():
    data = load_fixture()
    assert data.version == "retrieval-fixture-v1"
    assert len(data.chunks) == 15 and len(data.cases) == 9
    assert data.spec.model == "manual-vectors" and data.spec.dimensions == 6
    for mode in ("cosine", "lexical"):
        for k in (1, 3):
            report = evaluate(data.chunks, data.cases, k=k, mode=mode)
            assert report == evaluate(tuple(reversed(data.chunks)), data.cases, k=k, mode=mode)
            assert report.answerable == 7 and report.no_labels == 2
            expected = {
                ("cosine", 1): (7 / 9, 11 / 14, 1),
                ("cosine", 3): (10 / 27, 1, 1),
                ("lexical", 1): (6 / 9, 5 / 7, 6 / 7),
                ("lexical", 3): (10 / 27, 1, 13 / 14),
            }[(mode, k)]
            assert (report.precision_all, report.recall_answerable, report.mrr_answerable) == pytest.approx(
                expected
            )
            assert report.unwanted_returns == min(k, 2)
            assert all(
                hit.key.tenant == case.principal.tenant
                for result, case in zip(report.results, data.cases, strict=True)
                for hit in result.hits
            )


@pytest.mark.parametrize("raw", [b"", b"{}", b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff", b" " * 65537])
def test_fixture_bytes_reject_invalid_boundaries(raw):
    with pytest.raises((ValueError, UnicodeError)):
        decode_fixture(raw)


@pytest.mark.parametrize("change", ["vectors", "active", "extra", "groups"])
def test_fixture_rejects_wrong_current_structure(change):
    data = json.loads(files("academy_retrieval").joinpath("fixture.json").read_text())
    row = data["documents"][0]
    if change == "vectors":
        row["vectors"] = []
    elif change == "active":
        row["active"] = "true"
    elif change == "extra":
        row["authority"] = "administrator"
    else:
        row["groups"] = ["ops", "ops"]
    with pytest.raises(ValueError):
        decode_fixture(json.dumps(data).encode())
