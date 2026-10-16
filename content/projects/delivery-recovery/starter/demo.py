"""Trusted local evidence only: uses generated schema/key on caller's disposable stores."""

import argparse
from contextlib import contextmanager
from collections.abc import Iterator
from importlib.metadata import version
import json
import os
from pathlib import Path
import uuid
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from sqlalchemy import Engine, text
from sqlalchemy.pool import QueuePool
from academy_ingestion_service import Datum, make_engine
from academy_ingestion_service.database import url_from_dsn
from academy_delivery_schema import check, inspect_state, upgrade
from academy_durable_outbox import Accepted, record
from academy_leased_worker import Failure, Policy, claim, settle
from academy_stream_delivery import RedisBroker, deliver
from academy_stream_delivery.contracts import stream
from academy_stream_delivery.envelope import encode
from academy_delivery_recovery import Pruned, inspect_dead, prune, redrive


@contextmanager
def stores() -> Iterator[tuple[Engine, RedisBroker, str]]:
    dsn, url = os.environ["ACADEMY_RECOVERY_DSN"], os.environ["ACADEMY_BROKER_URL"]
    admin = psycopg2.connect(dsn, connect_timeout=5)
    schema, namespace = "recovery_" + uuid.uuid4().hex, "r-" + uuid.uuid4().hex[:24]
    engine = None
    client = Redis.from_url(
        url, decode_responses=False, socket_timeout=2, socket_connect_timeout=2, retry=Retry(NoBackoff(), 0)
    )
    try:
        with admin, admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        values = parse_dsn(dsn)
        values["options"] = "-csearch_path=" + schema
        engine = make_engine(url_from_dsn(make_dsn(**values)))
        upgrade(engine)
        broker = RedisBroker(client)
        broker.setup(namespace, "effects")
        broker.setup(namespace, "audit")
        yield engine, broker, namespace
    finally:
        try:
            client.delete(stream(namespace))
        finally:
            client.close()
            if engine is not None:
                engine.dispose()
            admin.rollback()
            admin.autocommit = True
            try:
                with admin.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            finally:
                admin.close()


def observe() -> dict[str, object]:
    with stores() as (engine, broker, namespace):
        policy = Policy(lease_ms=60000, max_attempts=3, delays_ms=(0, 0))
        record(engine, namespace, [Datum("a", 1, 7)])
        old = claim(engine, namespace, policy)
        assert old is not None and settle(engine, old, Failure.POISON)
        job = inspect_dead(engine, namespace)[0]
        assert redrive(engine, job, approve=True)
        repeated = redrive(engine, job, approve=True)
        with engine.connect() as connection:
            kept_generation = connection.execute(text("SELECT generation FROM delivery_job")).scalar_one()
        fresh = claim(engine, namespace, policy)
        assert fresh is not None and fresh.generation == 2 and fresh.event == old.event
        stale = settle(engine, old, Accepted(old.event))
        id = broker.append(namespace, encode(fresh.event))
        assert settle(engine, fresh, Accepted(fresh.event))
        before_effect = prune(engine, broker, namespace, id, allow_loss=True)
        assert deliver(engine, broker, namespace, "effects", "reader").acknowledged
        before_audit = prune(engine, broker, namespace, id, allow_loss=True)
        assert deliver(engine, broker, namespace, "audit", "reader").acknowledged
        with engine.connect() as connection:
            before = tuple(connection.execute(text("SELECT * FROM delivery_inbox")).all())
        deleted = prune(engine, broker, namespace, id, allow_loss=True)
        length = broker.client.xlen(stream(namespace))
        again = prune(engine, broker, namespace, id, allow_loss=True)
        broker.append(namespace, encode(fresh.event, version=1))
        assert deliver(engine, broker, namespace, "effects", "reader").acknowledged
        assert deliver(engine, broker, namespace, "audit", "reader").acknowledged
        with engine.connect() as connection:
            effect = connection.execute(text("SELECT total,applied FROM delivery_effect")).one()
            generation, state = connection.execute(text("SELECT generation,state FROM delivery_job")).one()
            inbox_unchanged = tuple(connection.execute(text("SELECT * FROM delivery_inbox")).all()) == before
            counts = {
                table: connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
                for table in ("feed_record", "delivery_outbox", "delivery_inbox", "delivery_job")
            }
            server = connection.execute(text("SHOW server_version_num")).scalar_one()
        check(engine)
        schema = inspect_state(engine)
        assert isinstance(engine.pool, QueuePool)
        assert deleted is Pruned.REMOVED and again is Pruned.MISSING
        assert not repeated and not stale and inbox_unchanged
        return dict(
            schema="2026.10-delivery-recovery-v1",
            server_version=int(server),
            head=list(schema.revisions),
            redrive=dict(
                before=job.generation,
                ready=kept_generation,
                claimed=generation,
                state=state,
                repeated=repeated,
                stale_settlement=stale,
                maximum=job.maximum,
            ),
            pruning=dict(
                before_effect=before_effect.value,
                unread_group=before_audit.value,
                result=deleted.value,
                length=length,
                repeated=again.value,
            ),
            replay=dict(total=effect.total, applied=effect.applied, inbox_unchanged=inbox_unchanged),
            retained=counts,
            checked_out_connections=engine.pool.checkedout(),
            versions={
                name: version(name)
                for name in (
                    "academy-delivery-recovery-lab",
                    "academy-delivery-schema-lab",
                    "academy-stream-delivery-lab",
                    "redis",
                    "SQLAlchemy",
                    "alembic",
                )
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = observe()
    serialized = json.dumps(report, indent=2) + "\n"
    args.output.write_text(serialized)
    print(serialized, end="")


if __name__ == "__main__":
    main()
