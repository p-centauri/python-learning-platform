from importlib.resources import files
import os
import uuid
import psycopg2
from psycopg2 import sql
import pytest


@pytest.fixture
def db():
    dsn = os.environ.get("ACADEMY_PERSISTENCE_DSN")
    if not dsn:
        pytest.skip("PostgreSQL not evaluated: set ACADEMY_PERSISTENCE_DSN to a disposable database")
    schema = "lab_" + uuid.uuid4().hex
    conn = psycopg2.connect(dsn, connect_timeout=5)
    other = psycopg2.connect(dsn, connect_timeout=5)
    try:
        for client in (conn, other):
            client.set_session(isolation_level="READ COMMITTED", readonly=False, autocommit=False)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
                cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
                cur.execute(files("academy_ingestion_persistence").joinpath("schema.sql").read_text())
        with other:
            with other.cursor() as cur:
                cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        yield conn, other
    finally:
        conn.close()
        other.rollback()
        other.autocommit = True
        try:
            with other.cursor() as cur:
                cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        finally:
            other.close()
