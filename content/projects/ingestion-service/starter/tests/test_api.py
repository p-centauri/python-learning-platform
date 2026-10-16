import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from academy_ingestion_service import Cursor, Datum, create_app, ingest, read_page
from academy_ingestion_service.contracts import ConflictingDatum, Receipt
from test_contracts import request, TOKEN, OTHER

pytestmark = pytest.mark.postgres


def app(engine):
    return create_app(engine, {TOKEN: "feed", OTHER: "other"})


def body(*rows):
    return {"items": [{"id": id, "revision": revision, "value": value} for id, revision, value in rows]}


def test_commit_duplicates_visibility_and_response_allowlist(engine):
    api = app(engine)
    first = request(api, "POST", "/namespaces/feed/readings", body=body(("a", 1, 0), ("b", 1, 10)))
    assert first.status_code == 200 and first.json() == {"observed": 2, "inserted": 2, "duplicates": 0}
    repeated = request(api, "POST", "/namespaces/feed/readings", body=body(("a", 1, 0), ("a", 1, 0)))
    assert repeated.json() == {"observed": 2, "inserted": 0, "duplicates": 2}
    with engine.connect() as observer:
        assert observer.execute(text("SELECT value FROM feed_record ORDER BY id")).scalars().all() == [0, 10]
    page = request(api, "GET", "/namespaces/feed/readings")
    assert page.json() == {
        "items": [{"id": "a", "revision": 1, "value": 0}, {"id": "b", "revision": 1, "value": 10}],
        "next_cursor": None,
    }
    assert "ingested_at" not in page.text and "namespace" not in page.text
    assert engine.pool.checkedout() == 0


def test_late_conflict_whole_batch_rollback_and_reuse(engine):
    api = app(engine)
    request(api, "POST", "/namespaces/feed/readings", body=body(("saved", 1, 5)))
    failed = request(api, "POST", "/namespaces/feed/readings", body=body(("new", 1, 7), ("saved", 1, 9)))
    assert failed.status_code == 409 and failed.json() == {"detail": "reading identity conflicts"}
    result = request(api, "GET", "/namespaces/feed/readings").json()
    assert result["items"] == [{"id": "saved", "revision": 1, "value": 5}]
    assert request(api, "POST", "/namespaces/feed/readings", body=body(("new", 1, 7))).status_code == 200
    assert engine.pool.checkedout() == 0


def test_conflicting_new_batch_also_rolls_back_source(engine):
    api = app(engine)
    failed = request(api, "POST", "/namespaces/feed/readings", body=body(("a", 1, 1), ("a", 1, 2)))
    assert failed.status_code == 409
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM feed_source")).scalar_one() == 0
        assert conn.execute(text("SELECT count(*) FROM feed_record")).scalar_one() == 0


def test_namespace_permission_cannot_be_forged_through_body_or_cursor(engine):
    api = app(engine)
    assert (
        request(
            api, "POST", "/namespaces/other/readings", body=body(("secret", 1, 55)), token=OTHER
        ).status_code
        == 200
    )
    assert request(api, "GET", "/namespaces/other/readings").status_code == 403
    assert (
        request(
            api,
            "POST",
            "/namespaces/feed/readings",
            body={"items": [{"id": "a", "revision": 1, "value": 1, "namespace": "other"}]},
        ).status_code
        == 422
    )
    own = request(
        api, "GET", "/namespaces/feed/readings", params={"after_id": "secret", "after_revision": "1"}
    )
    assert own.status_code == 200 and own.json()["items"] == []
    assert engine.pool.checkedout() == 0


def test_pagination_orders_all_key_parts_and_never_duplicates(engine):
    api = app(engine)
    rows = [("b", 1, 4), ("a", 2, 2), ("a", 1, 1), ("c", 1, 5)]
    request(api, "POST", "/namespaces/feed/readings", body=body(*rows))
    first = request(api, "GET", "/namespaces/feed/readings", params={"limit": "2"}).json()
    assert [(r["id"], r["revision"]) for r in first["items"]] == [("a", 1), ("a", 2)]
    assert first["next_cursor"] == {"id": "a", "revision": 2}
    second = request(
        api, "GET", "/namespaces/feed/readings", params={"limit": "2", "after_id": "a", "after_revision": "2"}
    ).json()
    assert [(r["id"], r["revision"]) for r in second["items"]] == [("b", 1), ("c", 1)]
    assert second["next_cursor"] is None
    assert engine.pool.checkedout() == 0


@pytest.mark.parametrize(
    "params",
    [
        {"limit": "0"},
        {"limit": "33"},
        {"limit": "1.0"},
        {"limit": "true"},
        {"after_id": "a"},
        {"after_revision": "1"},
        {"after_id": "A", "after_revision": "1"},
        {"after_id": "a", "after_revision": "9"},
    ],
)
def test_invalid_query_is_422_without_leaks(engine, params):
    result = request(app(engine), "GET", "/namespaces/feed/readings", params=params)
    assert result.status_code == 422 and "password" not in result.text
    assert engine.pool.checkedout() == 0


def test_driver_error_rolls_back_and_is_private_503(engine):
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE feed_record ADD CONSTRAINT late_failure CHECK (id <> 'bad')"))
    api = app(engine)
    failed = request(api, "POST", "/namespaces/feed/readings", body=body(("good", 1, 1), ("bad", 1, 2)))
    assert failed.status_code == 503 and failed.json() == {"detail": "storage operation failed"}
    assert "late_failure" not in failed.text
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM feed_record")).scalar_one() == 0
    assert request(api, "POST", "/namespaces/feed/readings", body=body(("good", 1, 1))).status_code == 200
    assert engine.pool.checkedout() == 0


def test_commit_boundary_failure_prevents_success(engine):
    def fail(session):
        raise DBAPIError("commit boundary", {}, Exception("private diagnostic"))

    api = app(engine)
    event.listen(Session, "before_commit", fail)
    try:
        failed = request(api, "POST", "/namespaces/feed/readings", body=body(("a", 1, 1)))
        assert failed.status_code == 503 and "private diagnostic" not in failed.text
    finally:
        event.remove(Session, "before_commit", fail)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM feed_record")).scalar_one() == 0
    assert engine.pool.checkedout() == 0


def test_service_rejects_active_caller_session_without_ending_work(engine):
    with Session(engine) as session:
        session.execute(text("INSERT INTO feed_source VALUES ('caller')"))
        for operation in [lambda: ingest(session, "feed", []), lambda: read_page(session, "feed")]:
            with pytest.raises(ValueError):
                operation()
            assert session.in_transaction()
        session.commit()
    with engine.connect() as conn:
        assert conn.execute(text("SELECT namespace FROM feed_source")).scalars().all() == ["caller"]


def test_service_constraints_bounds_and_original_conflict(engine):
    with Session(engine) as session:
        for rows in [[None], [Datum("a", 1, 0)] * 65]:
            with pytest.raises(ValueError):
                ingest(session, "feed", rows)
            assert not session.in_transaction()
        assert ingest(session, "feed", [Datum("a", 1, 0)]) == Receipt(1, 1, 0)
        with pytest.raises(ConflictingDatum):
            ingest(session, "feed", [Datum("a", 1, 1)])
        assert not session.in_transaction()
        for limit in [True, 0, 33, 1.0]:
            with pytest.raises(ValueError):
                read_page(session, "feed", limit=limit)
        assert read_page(session, "feed", after=Cursor("a", 1)).items == ()


def test_max_batch_and_page_limit(engine):
    api = app(engine)
    rows = [(f"id-{n:02}", 1, n) for n in range(64)]
    result = request(api, "POST", "/namespaces/feed/readings", body=body(*rows))
    assert result.json()["inserted"] == 64
    result = request(api, "GET", "/namespaces/feed/readings", params={"limit": "32"}).json()
    assert len(result["items"]) == 32 and result["next_cursor"] == {"id": "id-31", "revision": 1}


def test_readiness_and_method_contract(engine):
    api = app(engine)
    assert request(api, "GET", "/ready", token=None).json() == {"status": "ready"}
    assert request(api, "DELETE", "/namespaces/feed/readings").status_code == 405
    assert request(api, "GET", "/namespaces/feed/readings").json() == {"items": [], "next_cursor": None}
    assert engine.pool.checkedout() == 0


def test_exhausted_pool_is_private_503_without_extra_connection(engine):
    from sqlalchemy import create_engine

    bounded = create_engine(engine.url, pool_size=1, max_overflow=0, pool_timeout=0.05)
    try:
        api = create_app(bounded, {TOKEN: "feed"})
        with bounded.connect():
            failed = request(api, "GET", "/ready", token=None)
            assert failed.status_code == 503 and failed.json() == {"detail": "storage operation failed"}
            assert bounded.pool.checkedout() == 1
        assert request(api, "GET", "/ready", token=None).status_code == 200
        assert bounded.pool.checkedout() == 0
    finally:
        bounded.dispose()
