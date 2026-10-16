import os
import uuid
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
import pytest
from academy_ingestion_service import make_engine
from academy_ingestion_service.database import url_from_dsn


@pytest.fixture
def engine():
    dsn = os.environ.get("ACADEMY_SCHEMA_DSN")
    if not dsn:
        pytest.skip("migration behavior not evaluated: choose an explicitly disposable PostgreSQL database")
    admin = psycopg2.connect(dsn, connect_timeout=5)
    schema = "migration_" + uuid.uuid4().hex
    selected = None
    try:
        with admin, admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        values = parse_dsn(dsn)
        values["options"] = "-csearch_path=" + schema
        selected = make_engine(url_from_dsn(make_dsn(**values)))
        yield selected
    finally:
        if selected is not None:
            selected.dispose()
        admin.rollback()
        admin.autocommit = True
        try:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        finally:
            admin.close()
