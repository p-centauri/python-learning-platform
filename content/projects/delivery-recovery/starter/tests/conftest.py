import os
import uuid
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
import pytest
from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from academy_ingestion_service import make_engine
from academy_ingestion_service.database import url_from_dsn
from academy_delivery_schema import upgrade
from academy_stream_delivery import RedisBroker
from academy_stream_delivery.contracts import stream


@pytest.fixture
def live():
    dsn = os.environ.get("ACADEMY_RECOVERY_DSN")
    url = os.environ.get("ACADEMY_BROKER_URL")
    if not dsn or not url:
        pytest.skip("recovery not evaluated: configure disposable PostgreSQL and Redis")
    admin = psycopg2.connect(dsn, connect_timeout=5)
    schema = "recovery_" + uuid.uuid4().hex
    namespace = "r-" + uuid.uuid4().hex[:24]
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
