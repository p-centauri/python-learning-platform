from collections.abc import Iterator
from contextlib import contextmanager
from sqlalchemy import Engine, text
from academy_delivery_release.rehearsal import store as prior_store
from academy_delivery_schema import check


@contextmanager
def store(dsn: str) -> Iterator[tuple[str, Engine, str]]:
    """Explicit caller-owned disposable lab DDL; never called by request/import/factory."""
    with prior_store(dsn) as owned:
        _, engine, _ = owned
        with engine.begin() as connection:
            connection.execute(
                text("""CREATE TABLE api_webhook_receipt (
                namespace text COLLATE "C" NOT NULL CHECK(namespace ~ '^[a-z][a-z0-9-]{0,31}$'),
                delivery_id text COLLATE "C" NOT NULL CHECK(delivery_id ~ '^[a-z][a-z0-9-]{0,31}$'),
                body_digest text NOT NULL CHECK(body_digest ~ '^[0-9a-f]{64}$'),
                PRIMARY KEY(namespace, delivery_id))""")
            )
        try:
            yield owned
        finally:
            with engine.begin() as connection:
                connection.execute(text("DROP TABLE api_webhook_receipt"))
            check(engine)  # Original head and metadata remain unchanged after fixture cleanup.
