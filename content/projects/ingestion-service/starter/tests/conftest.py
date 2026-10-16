import os
import uuid
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn
import pytest
from sqlalchemy import URL
from academy_ingestion_service import make_engine, upgrade


@pytest.fixture
def base_engine():
    dsn = os.environ.get("ACADEMY_SERVICE_DSN")
    if not dsn:
        pytest.skip("PostgreSQL not evaluated: set ACADEMY_SERVICE_DSN to a disposable database")
    values = parse_dsn(dsn)
    schema = "service_" + uuid.uuid4().hex
    admin = psycopg2.connect(dsn, connect_timeout=5)
    engine = None
    try:
        with admin:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        url = URL.create(
            "postgresql+psycopg2",
            username=values.get("user"),
            password=values.get("password"),
            host=values.get("host"),
            port=int(values.get("port", "5432")),
            database=values.get("dbname"),
            query={"options": "-csearch_path=" + schema},
        )
        engine = make_engine(url)
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


@pytest.fixture
def engine(base_engine):
    upgrade(base_engine)
    return base_engine
