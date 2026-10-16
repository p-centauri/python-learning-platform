from dataclasses import replace
import sqlite3
import pytest
from academy_rag import Index, Record, publish
from academy_rag.fixtures import SPEC, record
from academy_retrieval import Principal
from academy_tools import Authority, Call, Store, approval_for, execute
from academy_tools.fixtures import setup


def test_read_write_and_persisted_new_call_id_replay(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    read = Call("r", "source_excerpt", "e0")
    assert execute(ctx, read, index, store, lambda: a).text == ctx.citations[0].span.text
    call = Call("w", "save_note", "e0", "Review file cleanup")
    first = execute(ctx, call, index, store, lambda: a)
    assert first.reason == "written" and first.note_id == 1 and store.counts(ctx) == (1, 1)
    reopened = Store(store.path)
    reopened.initialize()
    again = execute(ctx, replace(call, id="new-model-id"), index, reopened, lambda: a)
    assert again.reason == "replayed" and again.note_id == first.note_id and again.replayed
    assert reopened.counts(ctx) == (1, 1)


@pytest.mark.parametrize(
    "change", ["read", "actor", "tenant", "groups", "approval", "changed-label", "operation", "unknown-id"]
)
def test_application_scope_and_exact_approval(tmp_path, change):
    index, store, ctx, a = setup(tmp_path)
    call = Call("w", "save_note", "e0", "Review file cleanup")
    if change == "read":
        a = replace(a, read=False)
    if change == "actor":
        a = replace(a, actor="other")
    if change == "tenant":
        a = replace(a, principal=Principal("foreign", ("ops",)))
    if change == "groups":
        a = replace(a, principal=Principal("alpha"))
    if change == "approval":
        a = replace(a, approval=None)
    if change == "changed-label":
        call = replace(call, label="Different action")
    if change == "operation":
        ctx = replace(ctx, operation_id="another-operation")
    if change == "unknown-id":
        call = replace(call, citation="missing")
    result = execute(ctx, call, index, store, lambda: a)
    assert result.reason == (
        {
            "approval": "approval_required",
            "changed-label": "approval_required",
            "operation": "approval_required",
            "unknown-id": "unknown_citation",
        }.get(change, "forbidden")
    )
    assert store.counts(ctx) == (0, 0) and result.text is None


@pytest.mark.parametrize("change", ["update", "delete", "acl", "inactive"])
def test_current_source_rechecked_for_writes_and_replays(tmp_path, change):
    index, store, ctx, a = setup(tmp_path)
    call = Call("w", "save_note", "e0", "Review file cleanup")
    assert execute(ctx, call, index, store, lambda: a).reason == "written"
    owner = Index(index.path, SPEC)
    item = record(revision=2, text="Updated file cleanup")
    if change == "delete":
        item = Record("alpha", "files", 2, None)
    if change == "acl":
        item = record(revision=2, groups=("private",))
    if change == "inactive":
        item = record(revision=2, active=False)
    publish(owner, item)
    result = execute(ctx, replace(call, id="retry"), index, store, lambda: a)
    assert result.reason == "stale_source" and result.note_id is None and store.counts(ctx) == (1, 1)


def test_conflicting_reapproved_payload_cannot_reuse_committed_operation(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    call = Call("w", "save_note", "e0", "Review file cleanup")
    execute(ctx, call, index, store, lambda: a)
    changed = replace(call, label="A newly approved label")
    a = replace(a, approval=approval_for(ctx, changed))
    result = execute(ctx, changed, index, store, lambda: a)
    assert result.reason == "operation_conflict" and store.counts(ctx) == (1, 1)


def test_atomic_effect_receipt_limit_and_duplicate_at_limit(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    ctx = replace(ctx, max_notes=1)
    call = Call("w", "save_note", "e0", "Review file cleanup")
    assert execute(ctx, call, index, store, lambda: a).reason == "written"
    assert execute(ctx, replace(call, id="retry"), index, store, lambda: a).reason == "replayed"
    next_ctx = replace(ctx, operation_id="next")
    next_a = replace(a, approval=approval_for(next_ctx, call))
    assert execute(next_ctx, call, index, store, lambda: next_a).reason == "effect_limit"
    assert store.counts(ctx) == (1, 1)


def test_late_receipt_sql_failure_rolls_back_note(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    with sqlite3.connect(store.path) as db:
        db.execute(
            "CREATE TRIGGER receipt_failure BEFORE INSERT ON receipts BEGIN SELECT RAISE(ABORT,'fixture failure'); END"
        )
    result = execute(ctx, Call("w", "save_note", "e0", "Review file cleanup"), index, store, lambda: a)
    assert result.reason == "store_error" and store.counts(ctx) == (0, 0)
    with sqlite3.connect(store.path) as db:
        db.execute("DROP TRIGGER receipt_failure")
    assert (
        execute(ctx, Call("retry", "save_note", "e0", "Review file cleanup"), index, store, lambda: a).reason
        == "written"
    )


def test_receipts_are_tenant_actor_scoped(tmp_path):
    index, store, ctx, a = setup(tmp_path)
    call = Call("w", "save_note", "e0", "Review file cleanup")
    execute(ctx, call, index, store, lambda: a)
    other = replace(ctx, actor="another")
    other_a = Authority(other.principal, other.actor, True, approval_for(other, call))
    assert execute(other, call, index, store, lambda: other_a).reason == "written"
    assert store.counts(ctx) == store.counts(other) == (1, 1)


def test_store_constructor_quiet_initialize_explicit_and_schema_rejected(tmp_path):
    path = tmp_path / "separate.sqlite"
    store = Store(path)
    assert not path.exists()
    store.initialize()
    store.initialize()
    with sqlite3.connect(path) as db:
        db.execute("UPDATE metadata SET version='other-v2'")
    with pytest.raises(ValueError):
        store.initialize()
