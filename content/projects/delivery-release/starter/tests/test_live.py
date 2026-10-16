import json
import os
import signal
import socket
import subprocess
import sys
import time
from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.pool import QueuePool
from academy_delivery_release import Reason, Settings, StartupRefused, assess, create_release
from academy_delivery_schema import check, downgrade, upgrade
from academy_ingestion_service import Datum, create_app
from academy_durable_outbox import Event, consume, record
from academy_leased_worker import Policy, claim
from academy_ingestion_service.database import make_engine, url_from_dsn

TOKEN = "release_token_123456"


def configured(live):
    dsn, engine, namespace = live
    return Settings(dsn, ((TOKEN, namespace),))


def test_expected_head_and_unchanged_old_binary(live):
    _, engine, _ = live
    check(engine)
    assert assess(engine).reason is Reason.READY
    with TestClient(create_app(engine, {TOKEN: "feed"})) as old:
        assert old.get("/ready").status_code == 503
    assert isinstance(engine.pool, QueuePool) and engine.pool.checkedout() == 0


def test_factory_is_lazy_and_does_not_connect(live):
    settings = configured(live)
    with patch("academy_delivery_release.operations.assess", return_value=type(assess(live[1]))(Reason.READY)) as probe:
        release = create_release(settings)
        probe.assert_not_called()
        with TestClient(release.app) as client:
            assert client.get("/health").status_code == 200
        assert release.stop.is_set()


def test_permissions_strict_input_zero_and_output_preserved(live):
    _, engine, namespace = live
    with TestClient(create_release(configured(live)).app) as client:
        path = f"/namespaces/{namespace}/readings"
        assert client.get(path).status_code == 401
        assert client.get("/namespaces/other/readings", headers={"Authorization": "Bearer " + TOKEN}).status_code == 403
        headers = {"Authorization": "Bearer " + TOKEN}
        assert client.post(path, headers=headers, json={"items": [{"id": "a", "revision": 1, "value": 0}]}).status_code == 200
        result = client.get(path, headers=headers)
        assert result.status_code == 200 and result.headers["Cache-Control"] == "no-store"
        assert result.json()["items"] == [{"id": "a", "revision": 1, "value": 0}]
        assert client.post(path, headers=headers, json={"items": [], "unknown": 1}).status_code == 422
        assert client.get("/ready").json() == {"status": "ready", "reason": "ready"}
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM delivery_outbox")).scalar_one() == 0


def test_head_change_after_start_is_observed_without_breaking_liveness(live):
    _, engine, _ = live
    with TestClient(create_release(configured(live)).app) as client:
        assert client.get("/ready").status_code == 200
        with engine.begin() as connection:
            connection.execute(text("UPDATE alembic_version SET version_num='delivery_003'"))
        assert client.get("/ready").json()["reason"] == "schema-head"
        assert client.get("/ready").status_code == 503
        assert client.get("/health").status_code == 200
        with engine.begin() as connection:
            connection.execute(text("UPDATE alembic_version SET version_num='delivery_004'"))
        assert client.get("/ready").status_code == 200


def test_required_column_absence_is_finite_schema_contract(live):
    _, engine, _ = live
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE feed_record RENAME COLUMN ingested_at TO missing_column"))
    assert assess(engine).reason is Reason.SCHEMA_CONTRACT
    with pytest.raises(StartupRefused, match="schema-contract"):
        with TestClient(create_release(configured(live)).app):
            pass


def test_preflight_failure_disposes_owned_engine_once(live):
    _, engine, _ = live
    downgrade(engine, "delivery_003", allow_loss=True)
    owned = make_engine(url_from_dsn(live[0]))
    with patch("academy_delivery_release.operations.make_engine", return_value=owned), patch.object(owned, "dispose", wraps=owned.dispose) as disposal:
        with pytest.raises(StartupRefused, match="schema-head"):
            with TestClient(create_release(configured(live)).app):
                pass
        assert disposal.call_count == 1


def test_normal_lifetime_disposes_exactly_once(live):
    owned = make_engine(url_from_dsn(live[0]))
    with patch("academy_delivery_release.operations.make_engine", return_value=owned), patch.object(owned, "dispose", wraps=owned.dispose) as disposal:
        release = create_release(configured(live))
        with TestClient(release.app):
            assert disposal.call_count == 0
        assert disposal.call_count == 1 and release.stop.is_set()
        with patch("academy_delivery_release.operations.assess") as probe:
            with pytest.raises(StartupRefused, match="stopping"):
                with TestClient(release.app):
                    pass
            probe.assert_not_called()
        assert disposal.call_count == 1


def test_explicit_stop_refuses_new_business_and_readiness(live):
    release = create_release(configured(live))
    with TestClient(release.app) as client:
        release.stop.set()
        assert client.get("/health").status_code == 200
        assert client.get("/ready").json() == {"status": "not-ready", "reason": "stopping"}
        assert client.get("/ready").status_code == 503
        assert client.get(f"/namespaces/{live[2]}/readings").status_code == 503


def test_storage_failure_after_start_returns_safe_reason(live):
    release = create_release(configured(live))
    # Supplied fixture swaps only the owned readiness engine for a refused loopback destination.
    with TestClient(release.app) as client:
        unreachable = make_engine(url_from_dsn("host=127.0.0.1 port=1 dbname=absent user=lab password=secret"))
        try:
            assert assess(unreachable).reason is Reason.STORAGE_UNAVAILABLE
            with patch("academy_delivery_release.operations.assess", side_effect=lambda engine: assess(unreachable)):
                response = client.get("/ready")
                assert response.status_code == 503 and response.json()["reason"] == "storage-unavailable"
                assert "secret" not in response.text and client.get("/health").status_code == 200
            env = dict(os.environ, ACADEMY_RELEASE_DSN="host=127.0.0.1 port=1 dbname=absent user=lab password=secret", ACADEMY_RELEASE_TOKENS=json.dumps({TOKEN: live[2]}))
            env.pop("PYTHONPATH", None)
            result = subprocess.run([sys.executable, "-m", "academy_delivery_release.operate", "check"], env=env, cwd=os.path.dirname(sys.executable), capture_output=True, text=True, timeout=8)
            assert result.returncode == 1 and "storage-unavailable" in result.stderr
            assert "password" not in result.stderr and TOKEN not in result.stderr
        finally:
            unreachable.dispose()


@pytest.mark.parametrize("target", ["delivery_003", "service_002"])
def test_stopped_rollback_names_preserved_facts_and_lost_history(live, target):
    _, engine, namespace = live
    record(engine, namespace, [Datum("a", 1, 0)])
    event = Event(namespace, "a", 1, 0)
    consume(engine, event)
    assert claim(engine, namespace, Policy(60000, 3, (0, 0))) is not None
    with engine.connect() as connection:
        before = tuple(connection.execute(text("SELECT * FROM feed_record")).all())
    with TestClient(create_release(configured(live)).app):
        pass
    downgrade(engine, target, allow_loss=True)
    with engine.connect() as connection:
        assert tuple(connection.execute(text("SELECT * FROM feed_record")).all()) == before
        assert connection.execute(text("SELECT to_regclass('delivery_job')")).scalar_one() is None
        assert (connection.execute(text("SELECT to_regclass('delivery_inbox')")).scalar_one() is not None) == (target == "delivery_003")
    with pytest.raises(StartupRefused):
        with TestClient(create_release(configured(live)).app):
            pass
    upgrade(engine)
    check(engine)
    with TestClient(create_release(configured(live)).app) as client:
        assert client.get("/ready").status_code == 200
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM delivery_job")).scalar_one() == 0
        assert connection.execute(text("SELECT count(*) FROM delivery_inbox")).scalar_one() == (1 if target == "delivery_003" else 0)


def test_finite_lifetime_events_have_no_private_configuration(live, caplog):
    with caplog.at_level("INFO", logger="academy_delivery_release"):
        with TestClient(create_release(configured(live)).app):
            pass
    records = [json.loads(r.message) for r in caplog.records if r.name == "academy_delivery_release"]
    assert [r["event"] for r in records] == ["startup-ready", "stopping", "disposed"]
    assert TOKEN not in caplog.text and live[0] not in caplog.text


def test_installed_loopback_process_serves_then_sigterm_releases_connections(live, tmp_path):
    dsn, engine, namespace = live
    env = dict(os.environ, ACADEMY_RELEASE_DSN=dsn, ACADEMY_RELEASE_TOKENS=json.dumps({TOKEN: namespace}))
    env.pop("PYTHONPATH", None)
    with socket.socket() as selected:
        selected.bind(("127.0.0.1", 0))
        port = selected.getsockname()[1]
    def command(*arguments):
        return subprocess.run([sys.executable, "-m", "academy_delivery_release.operate", *arguments], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10)
    assert command("prepare").returncode == 0
    assert command("check").returncode == 0
    output = tmp_path / "server.log"
    with output.open("w") as log:
        process = subprocess.Popen([sys.executable, "-m", "academy_delivery_release.operate", "serve", "--port", str(port)], cwd=tmp_path, env=env, stdout=log, stderr=log)
        try:
            url = f"http://127.0.0.1:{port}"
            with httpx.Client(timeout=1, trust_env=False) as client:
                deadline = time.monotonic() + 10
                while True:
                    try:
                        if client.get(url + "/ready").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    assert process.poll() is None and time.monotonic() < deadline, "owned server did not become ready"
                    time.sleep(0.05)
                assert client.get(url + "/health").status_code == 200
                assert client.get(url + f"/namespaces/{namespace}/readings").status_code == 401
                assert client.get(url + f"/namespaces/{namespace}/readings", headers={"Authorization": "Bearer " + TOKEN}).status_code == 200
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=5)
            assert process.returncode in (0, -signal.SIGTERM)
            with engine.connect() as connection:
                application = connection.execute(text("SELECT current_setting('application_name')")).scalar_one()
                # Fixture and parent engine remain owned; every other tagged backend must have gone.
                assert connection.execute(text("SELECT count(*) FROM pg_stat_activity WHERE application_name=:app AND pid <> pg_backend_pid()"), {"app": application}).scalar_one() == 0
            with httpx.Client(timeout=0.3, trust_env=False) as client:
                with pytest.raises(httpx.TransportError):
                    client.get(url + "/health")
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
    assert command("rollback", "--target", "delivery_003", "--allow-loss").returncode == 0
    assert command("check").returncode == 1
    assert command("prepare").returncode == 0
    assert command("check").returncode == 0
    text_log = output.read_text()
    assert TOKEN not in text_log and dsn not in text_log and '"event": "disposed"' in text_log


def test_cli_loss_flag_required_before_connection(live, tmp_path):
    env = dict(os.environ, ACADEMY_RELEASE_DSN=live[0], ACADEMY_RELEASE_TOKENS=json.dumps({TOKEN: live[2]}))
    env.pop("PYTHONPATH", None)
    result = subprocess.run([sys.executable, "-m", "academy_delivery_release.operate", "rollback", "--target", "service_002"], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=5)
    assert result.returncode == 2 and "requires a named target" in result.stderr
    assert assess(live[1]).ready


def test_pool_exhaustion_is_safe_and_releases_borrowed_connections(live):
    from sqlalchemy import create_engine
    engine = create_engine(url_from_dsn(live[0]), isolation_level="READ COMMITTED", pool_size=1, max_overflow=0, pool_timeout=0.05)
    try:
        with engine.connect():
            assert assess(engine).reason is Reason.STORAGE_UNAVAILABLE
        assert assess(engine).ready and engine.pool.checkedout() == 0
    finally:
        engine.dispose()


def test_construction_failure_disposes_before_handoff(live):
    owned = make_engine(url_from_dsn(live[0]))
    with patch("academy_delivery_release.operations.make_engine", return_value=owned), patch("academy_delivery_release.operations.create_app", side_effect=RuntimeError("authored failure")), patch.object(owned, "dispose", wraps=owned.dispose) as disposal:
        with pytest.raises(RuntimeError, match="authored failure"):
            create_release(configured(live))
        assert disposal.call_count == 1


def test_settings_snapshot_cannot_change_existing_service_authority(live):
    settings = configured(live)
    release = create_release(settings)
    object.__setattr__(settings, "tokens", ((TOKEN, "other"),))
    with TestClient(release.app) as client:
        assert client.get(f"/namespaces/{live[2]}/readings", headers={"Authorization": "Bearer " + TOKEN}).status_code == 200
        assert client.get("/namespaces/other/readings", headers={"Authorization": "Bearer " + TOKEN}).status_code == 403


def test_startup_does_not_upgrade_an_old_head(live):
    downgrade(live[1], "service_002", allow_loss=True)
    release = create_release(configured(live))
    with pytest.raises(StartupRefused):
        with TestClient(release.app):
            pass
    with live[1].connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "service_002"
