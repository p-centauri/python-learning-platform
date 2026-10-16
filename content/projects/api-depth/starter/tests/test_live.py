from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from threading import Barrier
from fastapi.testclient import TestClient
from sqlalchemy import text
from academy_api_depth import create_app
from academy_api_depth.support import sign
from academy_ingestion_service import Datum, create_app as old_app
from academy_ingestion_service.service import ingest
from sqlalchemy.orm import Session

TOKEN = "local_test_token_12345"
SECRET = b"s" * 32
NOW = 1700000000
BODY = b'{"version":1,"id":"a","revision":1,"value":0}'


def auth():
    return {"Authorization": "Bearer " + TOKEN}


def signed(namespace, delivery="d", body=BODY, timestamp=NOW):
    return {
        "Content-Type": "application/json",
        "X-Delivery-ID": delivery,
        "X-Signed-At": str(timestamp),
        "X-Signature": sign(SECRET, namespace, delivery, str(timestamp), body),
    }


def count(engine, table):
    assert table in {"feed_record", "api_webhook_receipt", "delivery_outbox"}
    with engine.connect() as connection:
        return connection.execute(text("SELECT count(*) FROM " + table)).scalar_one()


def test_etag_exact_bytes_empty_weak_list_wildcard_and_change(live):
    _, engine, n = live
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: NOW)) as api:
        path = f"/v1/namespaces/{n}/snapshot"
        first = api.get(path, headers=auth())
        tag = first.headers["etag"]
        assert first.status_code == 200 and tag == '"' + sha256(first.content).hexdigest() + '"'
        assert first.json()["items"] == [] and first.headers["cache-control"] == "private, no-cache"
        for header in [tag, "W/" + tag, '"other", W/' + tag, "*"]:
            reply = api.get(path, headers={**auth(), "If-None-Match": header})
            assert reply.status_code == 304 and reply.content == b""
            assert reply.headers["etag"] == tag and reply.headers["vary"] == "Authorization"
            assert "content-type" not in reply.headers
        with Session(engine) as session:
            ingest(session, n, [Datum("a", 1, 0)])
        changed = api.get(path, headers={**auth(), "If-None-Match": tag})
        assert changed.status_code == 200 and changed.headers["etag"] != tag
        assert changed.json()["items"] == [dict(id="a", revision=1, value=0)]
    assert engine.pool.checkedout() == 0


def test_permission_precedes_conditional_validation_and_store(live):
    _, engine, n = live
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: NOW)) as api:
        for condition in ["*", "bad"]:
            for scope, headers, status in [(n, {}, 401), ("other", auth(), 403)]:
                result = api.get(
                    f"/v1/namespaces/{scope}/snapshot", headers={**headers, "If-None-Match": condition}
                )
                assert result.status_code == status and "etag" not in result.headers
                assert result.headers["cache-control"] == "no-store"
        assert (
            api.get(f"/v1/namespaces/{n}/snapshot", headers={**auth(), "If-None-Match": "bad"}).status_code
            == 400
        )
        # A failed store cannot produce a success/304 or a raw SQL error.
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE feed_record RENAME TO hidden_record"))
        try:
            denied = api.get(f"/v1/namespaces/{n}/snapshot", headers={"If-None-Match": "*"})
            assert denied.status_code == 401
            failed = api.get(f"/v1/namespaces/{n}/snapshot", headers={**auth(), "If-None-Match": "*"})
            assert failed.status_code == 503 and failed.json() == {"detail": "storage operation failed"}
            assert "etag" not in failed.headers
        finally:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE hidden_record RENAME TO feed_record"))
    assert engine.pool.checkedout() == 0


def test_route_limit_scope_and_equal_value_order(live):
    _, engine, n = live
    with Session(engine) as session:
        ingest(session, n, [Datum("b", 1, 0), Datum("a", 2, 0), Datum("a", 1, 0)])
    with Session(engine) as session:
        ingest(session, "other", [Datum("private", 1, 9)])
    with TestClient(
        create_app(engine, {TOKEN: n, "another_local_token_12345": "other"}, {n: SECRET}, clock=lambda: NOW)
    ) as api:
        path = f"/v1/namespaces/{n}/snapshot"
        one = api.get(path + "?limit=1", headers=auth())
        two = api.get(path + "?limit=2", headers=auth())
        assert one.json()["items"] == [dict(id="a", revision=1, value=0)]
        assert one.json()["next_cursor"] == dict(id="a", revision=1)
        assert two.json()["items"] == [dict(id="a", revision=1, value=0), dict(id="a", revision=2, value=0)]
        assert one.headers["etag"] != two.headers["etag"]
        other = api.get(
            "/v1/namespaces/other/snapshot", headers={"Authorization": "Bearer another_local_token_12345"}
        )
        assert other.headers["etag"] != one.headers["etag"] and other.json()["items"][0]["id"] == "private"
        for query in ["limit=0", "limit=33", "limit=01", "limit=1&limit=2", "unexpected=x"]:
            assert api.get(path + "?" + query, headers=auth()).status_code == 422


def test_committed_receipt_lost_reply_and_resigned_duplicate(live):
    _, engine, n = live
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: NOW)) as api:
        path = f"/v1/namespaces/{n}/webhooks"
        # Discard the first reply, as a sender with an uncertain network result would.
        api.post(path, headers=signed(n), content=BODY)
        reply = api.post(path, headers=signed(n, timestamp=NOW + 1), content=BODY)
        assert reply.status_code == 200 and reply.json()["duplicate"] is True
        assert count(engine, "api_webhook_receipt") == count(engine, "feed_record") == 1
        assert count(engine, "delivery_outbox") == 0
        assert reply.headers["cache-control"] == "no-store"
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT body_digest FROM api_webhook_receipt")).scalar_one()
                == sha256(BODY).hexdigest()
            )
    assert engine.pool.checkedout() == 0


def test_same_delivery_changed_raw_body_conflicts_even_equal_json(live):
    _, engine, n = live
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: NOW)) as api:
        path = f"/v1/namespaces/{n}/webhooks"
        assert api.post(path, headers=signed(n), content=BODY).status_code == 200
        changed = BODY + b" "
        result = api.post(path, headers=signed(n, body=changed), content=changed)
        assert result.status_code == 409 and result.json() == {"detail": "delivery identity conflicts"}
        assert count(engine, "api_webhook_receipt") == count(engine, "feed_record") == 1


def test_same_reading_new_delivery_receipt_and_conflict_rollback(live):
    _, engine, n = live
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: NOW)) as api:
        path = f"/v1/namespaces/{n}/webhooks"
        assert api.post(path, headers=signed(n), content=BODY).json()["duplicate"] is False
        assert api.post(path, headers=signed(n, "second"), content=BODY).json()["duplicate"] is False
        changed = BODY.replace(b'"value":0', b'"value":7')
        failed = api.post(path, headers=signed(n, "third", changed), content=changed)
        assert failed.status_code == 409 and failed.json() == {"detail": "reading identity conflicts"}
        assert count(engine, "api_webhook_receipt") == 2 and count(engine, "feed_record") == 1
        # Failure rolled the third receipt back: corrected content can use the same identity.
        assert api.post(path, headers=signed(n, "third"), content=BODY).status_code == 200
        assert count(engine, "api_webhook_receipt") == 3


def test_actual_competing_duplicates_one_new_receipt(live):
    _, engine, n = live
    app = create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: NOW)
    barrier = Barrier(2)

    def submit():
        with TestClient(app) as api:
            barrier.wait(timeout=3)
            result = api.post(f"/v1/namespaces/{n}/webhooks", headers=signed(n), content=BODY)
            assert result.status_code == 200
            return result.json()["duplicate"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit) for _ in range(2)]
        assert sorted(f.result(timeout=5) for f in futures) == [False, True]
    assert count(engine, "api_webhook_receipt") == count(engine, "feed_record") == 1
    assert engine.pool.checkedout() == 0


def test_stale_replay_rejected_before_duplicate_lookup(live):
    _, engine, n = live
    clock = [NOW]
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: clock[0])) as api:
        path = f"/v1/namespaces/{n}/webhooks"
        assert api.post(path, headers=signed(n), content=BODY).status_code == 200
        clock[0] += 301
        assert api.post(path, headers=signed(n), content=BODY).status_code == 401
        assert api.post(path, headers=signed(n, timestamp=clock[0]), content=BODY).json()["duplicate"] is True
        assert count(engine, "feed_record") == 1


def test_scope_signatures_malformed_event_and_payload_policy(live):
    _, engine, n = live
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET, "other": SECRET}, clock=lambda: NOW)) as api:
        path = f"/v1/namespaces/{n}/webhooks"
        assert api.post("/v1/namespaces/other/webhooks", headers=signed(n), content=BODY).status_code == 401
        assert api.post("/v1/namespaces/unknown/webhooks", headers=signed(n), content=BODY).status_code == 401
        bad = b"{"
        assert api.post(path, headers=signed(n, body=bad), content=bad).status_code == 422
        assert api.post(path, headers=signed(n), content=bad).status_code == 401
        assert api.post(path, headers=signed(n), content=b"x" * 4097).status_code == 413
        assert (
            api.post(path, headers={**signed(n), "Content-Type": "text/plain"}, content=BODY).status_code
            == 415
        )
        assert (
            api.post(path, headers={**signed(n), "Content-Encoding": "gzip"}, content=BODY).status_code == 415
        )
        headers = list(signed(n).items()) + [("X-Delivery-ID", "other")]
        assert api.post(path, headers=headers, content=BODY).status_code == 401
        assert count(engine, "api_webhook_receipt") == count(engine, "feed_record") == 0


def test_scope_copy_and_safe_logs(live, caplog):
    import logging

    _, engine, n = live
    tokens = {TOKEN: n}
    secrets = {n: SECRET}
    app = create_app(engine, tokens, secrets, clock=lambda: NOW)
    tokens.clear()
    secrets.clear()
    with caplog.at_level(logging.INFO, logger="academy_api_depth"), TestClient(app) as api:
        result = api.post(f"/v1/namespaces/{n}/webhooks", headers=signed(n), content=BODY)
        assert result.status_code == 200
        assert api.get(f"/v1/namespaces/{n}/snapshot", headers=auth()).status_code == 200
        assert len(result.headers["x-request-id"]) == 32
    own = [r for r in caplog.records if r.name == "academy_api_depth"]
    assert len(own) == 2
    assert TOKEN not in str([r.__dict__ for r in own]) and BODY.decode() not in str([r.__dict__ for r in own])
    assert all(r.getMessage() == "request_completed" for r in own)


def test_actual_receipt_lock_timeout_releases_and_retries(live):
    _, engine, n = live
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: NOW)) as api:
        with engine.connect() as blocker, blocker.begin():
            blocker.execute(text("LOCK TABLE api_webhook_receipt IN ACCESS EXCLUSIVE MODE"))
            result = api.post(f"/v1/namespaces/{n}/webhooks", headers=signed(n), content=BODY)
            assert result.status_code == 503 and result.json() == {"detail": "storage operation failed"}
        assert count(engine, "feed_record") == count(engine, "api_webhook_receipt") == 0
        assert api.post(f"/v1/namespaces/{n}/webhooks", headers=signed(n), content=BODY).status_code == 200
    assert engine.pool.checkedout() == 0


def test_previous_api_input_output_readiness_and_no_enqueue_preserved(live):
    _, engine, n = live
    with TestClient(old_app(engine, {TOKEN: n})) as old:
        assert old.get("/ready").status_code == 503
    with TestClient(create_app(engine, {TOKEN: n}, {n: SECRET}, clock=lambda: NOW)) as api:
        assert api.get("/ready").status_code == 200 and api.get("/health").status_code == 200
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE api_webhook_receipt RENAME TO hidden_receipt"))
        try:
            assert api.get("/ready").status_code == 503
            assert api.get("/health").status_code == 200
        finally:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE hidden_receipt RENAME TO api_webhook_receipt"))
        path = f"/namespaces/{n}/readings"
        assert api.post(
            path, headers=auth(), json={"items": [dict(id="a", revision=1, value=0)]}
        ).json() == dict(observed=1, inserted=1, duplicates=0)
        assert api.get(path, headers=auth()).json() == dict(
            items=[dict(id="a", revision=1, value=0)], next_cursor=None
        )
        assert api.get(path, headers=auth()).headers["cache-control"] == "no-store"
        assert api.get(path).status_code == 401
        assert count(engine, "api_webhook_receipt") == count(engine, "delivery_outbox") == 0
    assert engine.pool.checkedout() == 0
