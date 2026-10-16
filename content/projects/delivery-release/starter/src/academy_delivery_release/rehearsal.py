"""Supplied fixture ownership for disposable stores only, never production databases."""
from collections.abc import Iterator
from contextlib import contextmanager
import uuid
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
from sqlalchemy import Engine
from academy_ingestion_service import make_engine
from academy_ingestion_service.database import url_from_dsn
from academy_delivery_schema import upgrade


@contextmanager
def store(dsn: str) -> Iterator[tuple[str, Engine, str]]:
    admin = psycopg2.connect(dsn, connect_timeout=5)
    schema = "release_" + uuid.uuid4().hex
    namespace = "r-" + uuid.uuid4().hex[:24]
    engine = None
    try:
        with admin, admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        values = parse_dsn(dsn)
        values["options"] = "-csearch_path=" + schema + " -capplication_name=" + schema
        private_dsn = make_dsn(**values)
        engine = make_engine(url_from_dsn(private_dsn))
        upgrade(engine)
        yield private_dsn, engine, namespace
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
