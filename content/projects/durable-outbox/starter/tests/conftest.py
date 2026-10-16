import os
import uuid
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
import pytest
from academy_ingestion_service import make_engine, upgrade
from academy_ingestion_service.database import url_from_dsn
from academy_durable_outbox import install


@pytest.fixture
def engine():
    dsn = os.environ.get("ACADEMY_OUTBOX_DSN")
    if not dsn:
        pytest.skip("PostgreSQL not evaluated: explicitly configure ACADEMY_OUTBOX_DSN")
    admin = psycopg2.connect(dsn, connect_timeout=5)
    schema = "outbox_" + uuid.uuid4().hex
    engine = None
    try:
        with admin, admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        values = parse_dsn(dsn)
        values["options"] = "-csearch_path=" + schema
        engine = make_engine(url_from_dsn(make_dsn(**values)))
        upgrade(engine)
        install(engine)
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        admin.rollback()
        admin.autocommit = True
        try:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        finally:
            admin.close()
