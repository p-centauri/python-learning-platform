from dataclasses import asdict
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from academy_ingestion_service import Datum, ingest
from academy_delivery_schema import check
from academy_delivery_release import assess
from academy_query_analysis import Filter, Match, PlanQuery, Revision, Summary, explain, history, search, summarize
from academy_query_analysis.rehearsal import indexes, note, workload
from academy_query_analysis.support import read, resource


def write(source, namespace, items):
    with Session(source) as session:
        ingest(session, namespace, items)


def fixtures(live):
    source, query, namespace = live
    write(source, namespace, [Datum("a", 1, 0), Datum("a", 3, 7), Datum("a", 8, 2), Datum("b", 1, 2)])
    write(source, "other", [Datum("a", 8, 999)])
    note(query, namespace, "a", 1, "first", {"kind": "alert"})
    note(query, namespace, "a", 1, "second", {"kind": "alert"})
    note(query, namespace, "a", 8, "last", {"kind": "alert", "region": None})
    note(query, namespace, "b", 1, "last", {"kind": "alert", "region": ""})
    note(query, "other", "a", 8, "last", {"kind": "alert"})
    return source, query, namespace


def test_join_does_not_multiply_facts_or_cross_namespace(live):
    _, query, namespace = fixtures(live)
    assert summarize(query, namespace) == Summary(namespace, 4, 11, 3)
    assert summarize(query, "other") == Summary("other", 1, 999, 1)


def test_empty_existing_and_absent_sources_are_different(live):
    source, query, _ = live
    with source.begin() as connection:
        connection.execute(text("INSERT INTO feed_source VALUES ('empty')"))
    assert summarize(query, "empty") == Summary("empty", 0, 0, 0)
    assert summarize(query, "absent") is None


def test_windows_keep_zero_gap_and_previous_values(live):
    _, query, namespace = fixtures(live)
    assert history(query, namespace, "a") == (Revision(1,0,None,None,0,False), Revision(3,7,0,7,7,False), Revision(8,2,7,-5,9,True))
    assert history(query, "other", "a") == (Revision(8,999,None,None,999,True),)


def test_history_limit_applies_after_complete_window_and_is_ascending(live):
    _, query, namespace = fixtures(live)
    assert history(query, namespace, "a", limit=1) == (Revision(1,0,None,None,0,False),)
    assert history(query, namespace, "missing") == ()


def test_filtering_old_notes_cannot_resurrect_old_revision(live):
    source, query, namespace = fixtures(live)
    write(source, namespace, [Datum("a", 8, 2)])  # Exact duplicate does not add a row.
    assert search(query, namespace, Filter('{"kind":"alert"}')) == (Match("a",8,2), Match("b",1,2))
    with query.begin() as connection:
        connection.execute(text("DELETE FROM query_note WHERE namespace=:ns AND id='a' AND revision=8"), {"ns": namespace})
    assert search(query, namespace, Filter('{"kind":"alert"}')) == (Match("b",1,2),)


def test_json_null_missing_and_empty_text_are_distinct(live):
    _, query, namespace = fixtures(live)
    assert search(query, namespace, Filter('{"region":null}')) == (Match("a",8,2),)
    assert search(query, namespace, Filter('{"region":""}')) == (Match("b",1,2),)
    assert search(query, namespace, Filter('{"region":"west"}')) == ()


def test_bound_json_string_cannot_turn_into_sql(live):
    source, query, namespace = live
    write(source, namespace, [Datum("a",1,0), Datum("b",1,4)])
    value = "x' OR 1=1 --"
    note(query, namespace, "a", 1, "label", {"kind": value})
    filter = Filter('{"kind":"' + value + '"}')
    assert search(query, namespace, filter) == (Match("a",1,0),)
    assert summarize(query, namespace) == Summary(namespace,2,4,1)


def test_complete_foreign_key_rejects_annotation_for_wrong_revision(live):
    source, query, namespace = live
    write(source, namespace, [Datum("a",1,0)])
    with pytest.raises(DBAPIError) as caught:
        note(query, namespace, "a", 2, "label", {"kind":"alert"})
    assert caught.value.orig.pgcode == "23503"
    assert summarize(query, namespace) == Summary(namespace,1,0,0)


def test_object_and_size_constraints_are_actual_postgresql(live):
    source, query, namespace = live
    write(source, namespace, [Datum("a",1,0)])
    with pytest.raises(DBAPIError) as caught:
        note(query, namespace, "a", 1, "large", {"kind":"x" * 2000})
    assert caught.value.orig.pgcode == "23514"
    with pytest.raises(DBAPIError):
        with query.begin() as connection:
            connection.execute(text("INSERT INTO query_note VALUES (:ns,'a',1,'bad','[]'::jsonb)"), {"ns":namespace})


def test_read_transaction_refuses_writes_and_releases_after_error(live):
    _, query, _ = live
    with pytest.raises(DBAPIError) as caught:
        with read(query) as connection:
            connection.execute(text("CREATE TABLE forbidden(value integer)"))
    assert caught.value.orig.pgcode == "25006"
    assert isinstance(query.pool, QueuePool) and query.pool.checkedout() == 0
    with query.connect() as connection:
        assert connection.execute(text("SELECT to_regclass('forbidden')")).scalar_one() is None


def test_actual_statement_limit_rolls_back_and_pool_is_reusable(live):
    _, query, namespace = live
    with pytest.raises(DBAPIError) as caught:
        with read(query) as connection:
            connection.execute(text("SELECT pg_sleep(5)"))
    assert caught.value.orig.pgcode == "57014"
    assert summarize(query, namespace) is None
    assert query.pool.checkedout() == 0


def test_query_results_are_materialized_without_borrowed_session_or_pool(live):
    source, query, namespace = fixtures(live)
    result = search(query, namespace, Filter('{"kind":"alert"}'))
    query.dispose()
    assert result == (Match("a",8,2), Match("b",1,2))
    assert isinstance(query.pool, QueuePool) and query.pool.checkedout() == 0
    assert summarize(query, namespace).total == 11
    # Extra report tables are a separate schema; previous source migration comparison stays clean.
    check(source)
    assert assess(source).ready


def test_actual_plans_preserve_results_and_report_index_observations(live):
    source, query, namespace = live
    workload(source, query, namespace)
    def values(name, **parameters):
        with read(query) as connection:
            return tuple(connection.execute(text(resource(name)), {"namespace":namespace,"limit":32,**parameters}).all())
    before_range = values("range.sql", minimum=900000, maximum=900100)
    before_notes = values("notes.sql", filter='{"kind":"rare"}')
    before = explain(query, PlanQuery.RANGE, namespace)
    note_before = explain(query, PlanQuery.NOTES, namespace)
    indexes(source, query, create=True)
    try:
        after = explain(query, PlanQuery.RANGE, namespace)
        note_after = explain(query, PlanQuery.NOTES, namespace)
        wide = explain(query, PlanQuery.RANGE, namespace, minimum=0, maximum=1000000)
        assert values("range.sql", minimum=900000, maximum=900100) == before_range
        assert values("notes.sql", filter='{"kind":"rare"}') == before_notes
        assert len(before_range) == 32 and len(before_notes) == 10
        for plan in (before, after, note_before, note_after, wide):
            assert plan.actual_rows in (10,32) and plan.loops == 1 and plan.node_types
            assert plan.execution_ms >= 0 and plan.total_cost >= 0 and plan.shared_hits >= 0
            assert asdict(plan)["nodes"]
        with source.connect() as connection:
            index = connection.execute(text("SELECT indexdef FROM pg_indexes WHERE schemaname=current_schema() AND indexname='query_value_cover'")).scalar_one()
            assert "(namespace, value, id, revision)" in index
        with query.connect() as connection:
            index = connection.execute(text("SELECT indexdef FROM pg_indexes WHERE schemaname=current_schema() AND indexname='query_note_body_gin'")).scalar_one()
            assert "USING gin (body jsonb_path_ops)" in index
        # No exact plan/timing gate: preserve observed choices, never force enable_seqscan off.
    finally:
        indexes(source, query, create=False)
    check(source)
