from dataclasses import replace
import sqlite3
import pytest
from academy_rag import Index, Record, publish
from academy_rag.fixtures import SPEC, record


def index(tmp_path):
    store = Index(tmp_path / "index.db", SPEC)
    store.initialize()
    return store


def test_explicit_initialization_and_reopen(tmp_path):
    store = Index(tmp_path / "index.db", SPEC)
    assert not store.path.exists()
    with pytest.raises(sqlite3.OperationalError):
        store.snapshot()
    assert not store.path.exists()
    store.initialize()
    publish(store, record())
    assert Index(store.path, SPEC).snapshot() == store.snapshot()
    store.initialize()
    assert store.snapshot()[0] == 1


def test_exact_replay_and_delete_marker_prevents_old_reappearance(tmp_path):
    store = index(tmp_path)
    source = record()
    assert publish(store, source)
    assert not publish(store, source) and store.snapshot()[0] == 1
    tombstone = Record("alpha", "files", 2, None)
    assert publish(store, tombstone) and not publish(store, tombstone)
    assert Index(store.path, SPEC).snapshot() == (2, (tombstone,))
    with pytest.raises(ValueError, match="conflict"):
        publish(store, source)
    assert publish(store, record(revision=3))
    assert store.snapshot()[1][0].revision == 3


@pytest.mark.parametrize(
    "change",
    [
        {"text": "Different current file failure note."},
        {"groups": ("admin",)},
        {"active": False},
        {"values": (0.0, 1.0)},
        {"revision": 0},
    ],
)
def test_conflicting_or_invalid_revision_does_not_mutate_store(tmp_path, change):
    store = index(tmp_path)
    publish(store, record())
    before = store.snapshot()
    with pytest.raises(ValueError):
        publish(store, record(**change))
    assert store.snapshot() == before


def test_document_keys_include_tenant_and_updates_replace_all_metadata(tmp_path):
    store = index(tmp_path)
    publish(store, record())
    publish(store, record(tenant="beta"))
    publish(store, record(revision=2, groups=("ops",), text="New file failure procedure."))
    rows = store.snapshot()[1]
    assert [(r.tenant, r.revision) for r in rows] == [("alpha", 2), ("beta", 1)]
    assert rows[0].document.groups == ("ops",) and rows[0].document.text == "New file failure procedure."


def test_rollback_if_epoch_write_fails_after_document_write(tmp_path):
    store = index(tmp_path)
    publish(store, record())
    before = store.snapshot()
    with store.transaction(write=True) as db:
        db.execute(
            "CREATE TRIGGER stop_epoch BEFORE UPDATE ON academy_rag_meta BEGIN SELECT RAISE(ABORT,'fixture rollback'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        publish(store, record(revision=2))
    assert store.snapshot() == before
    with store.transaction(write=True) as db:
        db.execute("DROP TRIGGER stop_epoch")
    assert publish(store, record(revision=2))


@pytest.mark.parametrize("values", [(0.0, 0.0), (True, 0), (1.0,), (float("nan"), 1), (10**1000, 0)])
def test_invalid_vectors_fail_before_saved_mutation(tmp_path, values):
    store = index(tmp_path)
    before = store.snapshot()
    with pytest.raises(ValueError):
        publish(store, record(values=values))
    assert store.snapshot() == before


def test_identity_and_tombstone_vectors_are_strict():
    with pytest.raises(ValueError):
        replace(record(), tenant="other")
    with pytest.raises(ValueError):
        Record("alpha", "files", 2, None, ((1.0, 0.0),))


def test_document_and_chunk_caps_are_atomic(tmp_path):
    store = index(tmp_path)
    for n in range(16):
        publish(store, record(id="d" + str(n)))
    before = store.snapshot()
    with pytest.raises(ValueError, match="identity cap"):
        publish(store, record(id="overflow"))
    assert store.snapshot() == before
    large = Index(tmp_path / "large.db", SPEC)
    large.initialize()
    for n in range(2):
        publish(large, record(id="large" + str(n), text="file failure " + "x" * 1648))
    before = large.snapshot()
    with pytest.raises(ValueError, match="chunk cap"):
        publish(large, record(id="large2", text="file failure " + "x" * 1648))
    assert large.snapshot() == before


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE academy_rag_meta SET schema='unknown'",
        "UPDATE academy_rag_meta SET epoch=-1",
        "UPDATE academy_rag_meta SET spec=x'00'",
        "UPDATE academy_rag_docs SET payload=x'00'",
        "UPDATE academy_rag_docs SET revision=9",
    ],
)
def test_corrupt_store_fails_closed_without_repair(tmp_path, sql):
    store = index(tmp_path)
    publish(store, record())
    with store.transaction(write=True) as db:
        db.execute(sql)
    with pytest.raises(ValueError):
        store.snapshot()


def test_reopening_with_wrong_model_spec_never_rewrites_metadata(tmp_path):
    store = index(tmp_path)
    publish(store, record())
    before = store.snapshot()
    wrong = Index(store.path, replace(SPEC, version="other"))
    with pytest.raises(ValueError):
        wrong.initialize()
    assert store.snapshot() == before
