from collections.abc import Iterator
from contextlib import contextmanager
import uuid
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
from sqlalchemy import Engine
from academy_ingestion_service import make_engine, upgrade, check_migrations
from academy_ingestion_service.database import url_from_dsn


@contextmanager
def store(dsn: str) -> Iterator[Engine]:
    """Explicit disposable service_002 fixture; no DDL on imports/factories/requests."""
    schema = "practical_" + uuid.uuid4().hex
    admin = psycopg2.connect(dsn, connect_timeout=5)
    engine = None
    try:
        with admin, admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        values = parse_dsn(dsn)
        values["options"] = "-csearch_path=" + schema + " -capplication_name=" + schema
        engine = make_engine(url_from_dsn(make_dsn(**values)))
        upgrade(engine)
        yield engine
        check_migrations(engine)
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
