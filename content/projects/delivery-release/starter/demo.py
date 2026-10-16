"""Actual disposable PostgreSQL and broker release observations; guarded entry point."""
import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated.*", category=UserWarning)
    warnings.filterwarnings("ignore", message="The anyio.abc.BlockingPortal alias is deprecated.*", category=DeprecationWarning)
    from fastapi.testclient import TestClient
from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from sqlalchemy import text
from sqlalchemy.pool import QueuePool
from academy_delivery_release import Settings, StartupRefused, create_release
from academy_delivery_release.rehearsal import store
from academy_delivery_schema import check, downgrade, inspect_state, upgrade
from academy_ingestion_service import Datum, create_app
from academy_durable_outbox import Accepted, record
from academy_leased_worker import Failure, Policy, claim, settle
from academy_stream_delivery import RedisBroker, deliver
from academy_stream_delivery.contracts import stream
from academy_stream_delivery.envelope import encode
from academy_delivery_recovery import Pruned, inspect_dead, prune, redrive


def observe() -> dict[str, object]:
    token = "local_demo_token_12345"
    with store(os.environ["ACADEMY_RELEASE_TEST_DSN"]) as (dsn, engine, namespace):
        client = Redis.from_url(os.environ["ACADEMY_BROKER_URL"], decode_responses=False, socket_timeout=2, socket_connect_timeout=2, retry=Retry(NoBackoff(), 0))
        try:
            broker = RedisBroker(client)
            broker.setup(namespace, "effects")
            record(engine, namespace, [Datum("a", 1, 0)])
            policy = Policy(60000, 3, (0, 0))
            first = claim(engine, namespace, policy)
            assert first is not None and settle(engine, first, Failure.POISON)
            assert redrive(engine, inspect_dead(engine, namespace)[0], approve=True)
            fresh = claim(engine, namespace, policy)
            assert fresh is not None and fresh.generation == 2
            id = broker.append(namespace, encode(fresh.event))
            assert settle(engine, fresh, Accepted(fresh.event))
            assert deliver(engine, broker, namespace, "effects", "reader").acknowledged
            assert prune(engine, broker, namespace, id, allow_loss=True) is Pruned.REMOVED
            with TestClient(create_app(engine, {token: namespace})) as old:
                old_ready = old.get("/ready").status_code
            release = create_release(Settings(dsn, ((token, namespace),)))
            with TestClient(release.app) as api:
                initial = api.get("/ready").status_code
                unauthorized = api.get(f"/namespaces/{namespace}/readings").status_code
                permitted = api.get(f"/namespaces/{namespace}/readings", headers={"Authorization": "Bearer " + token}).status_code
                with engine.begin() as connection:
                    connection.execute(text("UPDATE alembic_version SET version_num='delivery_003'"))
                changed = api.get("/ready").status_code
                alive = api.get("/health").status_code
                with engine.begin() as connection:
                    connection.execute(text("UPDATE alembic_version SET version_num='delivery_004'"))
                restored = api.get("/ready").status_code
                release.stop.set()
                draining = api.get("/ready").status_code
                admission = api.get(f"/namespaces/{namespace}/readings").status_code
            with engine.connect() as connection:
                before = tuple(connection.execute(text("SELECT * FROM feed_record")).all())
                inbox_before = connection.execute(text("SELECT count(*) FROM delivery_inbox")).scalar_one()
                server = int(connection.execute(text("SHOW server_version_num")).scalar_one())
            downgrade(engine, "delivery_003", allow_loss=True)
            refused = False
            try:
                with TestClient(create_release(Settings(dsn, ((token, namespace),))).app):
                    pass
            except StartupRefused:
                refused = True
            upgrade(engine)
            check(engine)
            with TestClient(create_release(Settings(dsn, ((token, namespace),))).app) as api:
                restarted = api.get("/ready").status_code
            with engine.connect() as connection:
                unchanged = tuple(connection.execute(text("SELECT * FROM feed_record")).all()) == before
                jobs = connection.execute(text("SELECT count(*) FROM delivery_job")).scalar_one()
                inbox_after = connection.execute(text("SELECT count(*) FROM delivery_inbox")).scalar_one()
            assert isinstance(engine.pool, QueuePool)
            return dict(schema="2026.10-delivery-release-v1", head=list(inspect_state(engine).revisions), server_version=server,
                readiness=dict(old=old_ready, compatible=initial, changed=changed, alive=alive, restored=restored, draining=draining, admission=admission, restarted=restarted),
                permissions=dict(unauthorized=unauthorized, permitted=permitted),
                rollback=dict(refused=refused, facts_unchanged=unchanged, jobs_after=jobs, inbox_before=inbox_before, inbox_after=inbox_after),
                recovery=dict(generation=fresh.generation, payload_removed=client.xlen(stream(namespace)) == 0),
                checked_out_connections=engine.pool.checkedout(),
                versions={name: version(name) for name in ("academy-delivery-release-lab", "academy-delivery-recovery-lab", "academy-delivery-schema-lab", "fastapi", "uvicorn", "SQLAlchemy", "redis")})
        finally:
            try:
                client.delete(stream(namespace))
            finally:
                client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = observe()
    output = json.dumps(report, indent=2) + "\n"
    args.output.write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
