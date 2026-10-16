from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import files
from sqlalchemy import Connection, Engine, text
from psycopg2.extensions import connection as PsycopgConnection


def resource(name: str) -> str:
    if name not in {"summary.sql", "history.sql", "search.sql", "range.sql", "notes.sql"}:
        raise ValueError("fixed query required")
    return files("academy_query_analysis").joinpath(name).read_text()


@contextmanager
def read(engine: Engine) -> Iterator[Connection]:
    if engine.dialect.name != "postgresql" or engine.dialect.driver != "psycopg2":
        raise ValueError("PostgreSQL/psycopg2 required")
    with engine.connect() as connection, connection.begin():
        raw: object = connection.connection.dbapi_connection
        if not isinstance(raw, PsycopgConnection) or raw.autocommit or connection.get_isolation_level() != "READ COMMITTED":
            raise ValueError("non-autocommit READ COMMITTED required")
        connection.execute(text("SET TRANSACTION READ ONLY"))
        connection.execute(text("SET LOCAL lock_timeout = '250ms'"))
        connection.execute(text("SET LOCAL statement_timeout = '1000ms'"))
        yield connection
