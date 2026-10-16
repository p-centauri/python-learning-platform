import asyncio
from fastapi.testclient import TestClient
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session
from academy_ingestion_service import Datum, create_app, ingest, check_migrations
from academy_practical_review import analyse, prepare, read_all
from academy_practical_review.server import serving

TOKEN = "local_test_token_12345"


def test_actual_loopback_async_pages_to_latest_snapshot_and_equal_reports(live):
    rows = [
        Datum("item-" + str(i).zfill(2), revision, 0 if i == 0 and revision == 4 else i * 10 + revision)
        for i in range(32)
        for revision in range(1, 5)
    ]
    with Session(live) as session:
        for offset in (0, 64):
            ingest(session, "north", rows[offset : offset + 64])
    with live.connect() as connection:
        before = connection.execute(text("SELECT * FROM feed_record ORDER BY id,revision")).all()
    app = create_app(live, {TOKEN: "north"})
    with serving(app) as url:

        async def scenario():
            async with httpx.AsyncClient(base_url=url, timeout=5) as client:
                return await read_all(client, "north", TOKEN)

        observed = asyncio.run(scenario())
        assert observed == tuple(rows)
        items = prepare("north", observed)
        requests = tuple(range(8)) * 16 + tuple(range(8, 32))
        baseline = analyse(items, requests)
        candidate = analyse(items, requests, cached=True)
        assert len(items) == 32 and items[0].datum.value == 0
        assert baseline.snapshot == candidate.snapshot and baseline.fingerprints == candidate.fingerprints
        assert (baseline.computations, candidate.computations, candidate.hits) == (152, 32, 120)
    with live.connect() as connection:
        assert connection.execute(text("SELECT * FROM feed_record ORDER BY id,revision")).all() == before
    check_migrations(live)
    assert live.pool.checkedout() == 0


def test_old_service_success_duplicate_conflict_and_permissions_unchanged(live):
    with TestClient(create_app(live, {TOKEN: "north"})) as api:
        auth = {"Authorization": "Bearer " + TOKEN}
        path = "/namespaces/north/readings"
        body = {"items": [dict(id="a", revision=1, value=0)]}
        assert api.post(path, headers=auth, json=body).json() == dict(observed=1, inserted=1, duplicates=0)
        assert api.post(path, headers=auth, json=body).json() == dict(observed=1, inserted=0, duplicates=1)
        conflict = {"items": [dict(id="b", revision=1, value=5), dict(id="a", revision=1, value=7)]}
        assert api.post(path, headers=auth, json=conflict).status_code == 409
        assert api.get(path, headers=auth).json() == dict(
            items=[dict(id="a", revision=1, value=0)], next_cursor=None
        )
        assert api.get(path).status_code == 401
        assert api.get("/namespaces/other/readings", headers=auth).status_code == 403
        assert api.get(path, headers=auth).headers["cache-control"] == "no-store"
        assert api.get("/ready").status_code == 200
    check_migrations(live)
    assert live.pool.checkedout() == 0


def test_adapter_refuses_large_old_valid_value_without_changing_store(live):
    with Session(live) as session:
        ingest(session, "north", [Datum("a", 1, 1000000)])
    with TestClient(create_app(live, {TOKEN: "north"})) as api:
        reply = api.get("/namespaces/north/readings", headers={"Authorization": "Bearer " + TOKEN})
        assert reply.status_code == 200 and reply.json()["items"][0]["value"] == 1000000
    from academy_practical_review import decode_page
    import pytest

    with pytest.raises(ValueError):
        prepare("north", decode_page(reply.json()).items)
    with live.connect() as connection:
        assert connection.execute(text("SELECT value FROM feed_record")).scalar_one() == 1000000
    assert live.pool.checkedout() == 0
