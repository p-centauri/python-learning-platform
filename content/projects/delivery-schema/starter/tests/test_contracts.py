from importlib.resources import files
from unittest.mock import MagicMock
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine
import pytest
from academy_delivery_schema import HEAD, SchemaState, downgrade, upgrade
from academy_delivery_schema.metadata import metadata
from academy_ingestion_service.models import Base


@pytest.mark.parametrize(
    "revision", ["base", "service_001", "unknown", "heads", "head; DROP TABLE feed_record", None, 1]
)
def test_bad_upgrade_target_opens_no_connection(revision):
    engine = MagicMock(spec=Engine)
    with pytest.raises(ValueError):
        upgrade(engine, revision)
    engine.begin.assert_not_called()


@pytest.mark.parametrize("flag", [False, 1, "yes", None, [], object()])
def test_loss_flag_must_be_exact_true_before_database_access(flag):
    engine = MagicMock(spec=Engine)
    with pytest.raises(ValueError):
        downgrade(engine, "service_002", allow_loss=flag)
    engine.begin.assert_not_called()


@pytest.mark.parametrize("revision", ["base", "service_001", "head", "delivery_004", "unexpected"])
def test_forbidden_destructive_target_never_opens_database(revision):
    engine = MagicMock(spec=Engine)
    with pytest.raises(ValueError):
        downgrade(engine, revision, allow_loss=True)
    engine.begin.assert_not_called()


@pytest.mark.parametrize(
    "revisions,expected",
    [
        ((), False),
        (("service_002",), False),
        ((HEAD,), True),
        ((HEAD, "other"), False),
        (("unknown",), False),
    ],
)
def test_head_is_exact_revision_only(revisions, expected):
    assert SchemaState(revisions).at_head is expected


def test_combined_metadata_does_not_mutate_previous_service():
    assert set(Base.metadata.tables) == {"feed_source", "feed_record"}
    assert len(metadata.tables) == 7
    assert metadata.tables["feed_record"] is not Base.metadata.tables["feed_record"]
    assert {x.name for x in metadata.tables["delivery_job"].indexes} == {"delivery_job_ready"}
    assert metadata.tables["delivery_job"].c.generation.type.python_type is int


def test_single_packaged_chain_and_preserved_service_history():
    package = files("academy_delivery_schema")
    cfg = Config()
    cfg.set_main_option("script_location", str(package.joinpath("migrations")))
    scripts = ScriptDirectory.from_config(cfg)
    assert scripts.get_heads() == [HEAD]
    assert [r.revision for r in scripts.walk_revisions()] == [
        HEAD,
        "delivery_003",
        "service_002",
        "service_001",
    ]
    for filename in ["001_initial.py", "002_observed_at.py"]:
        assert (
            package.joinpath("migrations/versions/" + filename).read_bytes()
            == files("academy_ingestion_service").joinpath("migrations/versions/" + filename).read_bytes()
        )
