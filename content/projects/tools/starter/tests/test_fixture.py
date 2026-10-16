from dataclasses import replace
import pytest
from academy_tools import Call, approval_for
from academy_tools.fixtures import setup


def test_approval_binds_all_action_parameters_but_not_model_call_id(tmp_path):
    _, _, ctx, _ = setup(tmp_path)
    call = Call("original", "save_note", "e0", "Review file cleanup")
    digest = approval_for(ctx, call)
    assert approval_for(ctx, replace(call, id="model-retry")) == digest
    assert approval_for(ctx, replace(call, label="Changed label")) != digest
    assert approval_for(replace(ctx, actor="other"), call) != digest
    assert approval_for(replace(ctx, operation_id="other"), call) != digest


@pytest.mark.parametrize(
    "field,value", [("max_notes", True), ("task", ""), ("citations", ()), ("actor", "role/admin")]
)
def test_bounded_application_context(tmp_path, field, value):
    _, _, ctx, _ = setup(tmp_path)
    with pytest.raises(ValueError):
        replace(ctx, **{field: value})
