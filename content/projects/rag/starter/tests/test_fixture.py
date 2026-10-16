import asyncio
from dataclasses import replace
from importlib.metadata import version
from importlib.resources import files
from academy_model_contracts import Adapter, ModelConfig, build_request
from academy_retrieval.dataset import load_fixture
from academy_rag import Index, answer, prepare, publish
from academy_rag.fixtures import CONFIG, PRINCIPAL, QUERY, REQUIRED, SPEC, VERSION, Scripted, record


def test_published_package_composition_and_markers():
    assert version("academy-model-contracts-lab") == version("academy-retrieval-lab") == "0.1.0"
    assert files("academy_rag").joinpath("py.typed").is_file()
    prior = load_fixture()
    assert len(prior.cases) == 9
    assert build_request(ModelConfig(), "unchanged prior triage input").input_bound > 0
    assert VERSION == "rag-fixture-v1"


def test_supported_adapter_dialects_and_two_whole_excerpts(tmp_path):
    index = Index(tmp_path / "index.db", SPEC)
    index.initialize()
    publish(index, record(id="a"))
    publish(index, record(id="b", text="Close the file safely after a failure."))
    bundle = prepare(index, PRINCIPAL, QUERY, REQUIRED)
    for dialect in ("message-v1", "completion-v1"):
        config = replace(CONFIG, dialect=dialect)
        fake = Scripted("all")
        adapter = Adapter(config.provider_id, config.dialect, fake)
        result = asyncio.run(answer(index, bundle, lambda: PRINCIPAL, adapter, config))
        assert result.reason == "answered" and len(result.citations) == 2
        assert result.text == "\n".join(e.span.text for e in bundle.evidence[:2])
