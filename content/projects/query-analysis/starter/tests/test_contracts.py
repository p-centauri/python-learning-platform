from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from academy_query_analysis import Filter, PlanQuery, explain, history, search, summarize
from academy_query_analysis.plans import summarize_plan
from academy_query_analysis.support import read, resource


@pytest.mark.parametrize("document", ["{}", "[]", '"text"', '{"kind":true}', '{"kind":1}', '{"kind":[]}', '{"kind":"a","kind":"b"}', '{"unknown":"a"}', '{"kind":"' + 'x' * 33 + '"}', 'x' * 513])
def test_filter_rejects_wrong_duplicate_and_oversized_shapes(document):
    with pytest.raises(ValueError):
        Filter(document)


def test_json_null_and_empty_text_are_distinct_canonical_filters():
    assert Filter('{ "region" : null }').encoded == '{"region":null}'
    assert Filter('{"region":""}').encoded == '{"region":""}'


@pytest.mark.parametrize("limit", [True, 0, 33, -1])
def test_search_limit_rejected_before_connecting(limit):
    with patch("academy_query_analysis.operations.read") as owner:
        with pytest.raises(ValueError):
            search(None, "feed", Filter('{"kind":"alert"}'), limit=limit)
        owner.assert_not_called()


def test_invalid_scope_rejected_before_connecting():
    with patch("academy_query_analysis.operations.read") as owner:
        with pytest.raises(ValueError):
            summarize(None, "feed' OR 1=1")
        with pytest.raises(ValueError):
            history(None, "feed", "bad id")
        owner.assert_not_called()


def test_tampered_frozen_filter_is_revalidated():
    filter = Filter('{"kind":"alert"}')
    object.__setattr__(filter, "encoded", '{"kind":false}')
    with patch("academy_query_analysis.operations.read") as owner:
        with pytest.raises(ValueError):
            search(None, "feed", filter)
        owner.assert_not_called()


def test_explain_accepts_only_named_queries_before_connecting():
    with pytest.raises(ValueError):
        explain(None, "SELECT pg_sleep(99)", "feed")
    with pytest.raises(ValueError):
        explain(None, PlanQuery.RANGE, "feed", minimum=900001, maximum=2)
    with pytest.raises(ValueError):
        resource("../../private.sql")


def test_other_dialect_is_not_a_postgresql_evaluation():
    engine = create_engine("sqlite://")
    try:
        with pytest.raises(ValueError):
            with read(engine):
                pass
    finally:
        engine.dispose()


def test_plan_summary_uses_root_buffers_without_double_counting_children():
    node = {"Node Type": "Limit", "Plan Rows": 2, "Actual Rows": 2, "Actual Loops": 1, "Total Cost": 6, "Shared Hit Blocks": 5, "Shared Read Blocks": 1,
            "Plans": [{"Node Type": "Index Scan", "Index Name": "example", "Plan Rows": 100, "Actual Rows": 2, "Actual Loops": 1, "Total Cost": 100, "Shared Hit Blocks": 5}]}
    plan = summarize_plan([{"Plan": node, "Execution Time": 0.1}])
    assert plan.shared_hits == 5 and plan.shared_reads == 1
    assert plan.node_types == ("Limit", "Index Scan") and plan.indexes == ("example",)
    assert plan.nodes[1].estimated_rows == 100 and plan.total_cost == 6


@pytest.mark.parametrize("document", [None, [], [{}]])
def test_invalid_plan_document_is_not_invented_evidence(document):
    with pytest.raises(ValueError):
        summarize_plan(document)
