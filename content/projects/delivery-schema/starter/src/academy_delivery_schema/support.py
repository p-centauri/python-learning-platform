from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.resources import files
from io import StringIO
from alembic.config import Config
from sqlalchemy import Connection, Engine, inspect, text
from psycopg2.extensions import connection as PsycopgConnection
from academy_competing_ingestion.contracts import require_engine

HEAD = "delivery_004"
LOCK = 718419004  # Shared by this lab's cooperating migration clients, within one database.


class BusyMigration(RuntimeError):
    pass


class NotReady(RuntimeError):
    pass


@dataclass(frozen=True)
class SchemaState:
    revisions: tuple[str, ...]

    @property
    def at_head(self) -> bool:
        return self.revisions == (HEAD,)


def current(connection: Connection) -> SchemaState:
    if not inspect(connection).has_table("alembic_version"):
        return SchemaState(())
    values = (
        connection.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
        .scalars()
        .all()
    )
    if any(type(value) is not str for value in values):
        raise ValueError("invalid revision state")
    return SchemaState(tuple(values))


def inspect_state(engine: Engine) -> SchemaState:
    """Head only; no drift or data-validity claim. Caller owns the engine."""
    require_engine(engine)
    with engine.connect() as connection:
        return current(connection)


def target(revision: str, *, backwards: bool = False) -> None:
    choices = {"service_002", "delivery_003"} if backwards else {"service_002", "delivery_003", HEAD, "head"}
    if type(revision) is not str or revision not in choices:
        raise ValueError("unsupported explicit migration target")


@contextmanager
def migration(engine: Engine) -> Iterator[Config]:
    require_engine(engine)
    cfg = Config(stdout=StringIO())
    cfg.set_main_option("script_location", str(files("academy_delivery_schema").joinpath("migrations")))
    with engine.begin() as connection:
        raw: object = connection.connection.dbapi_connection
        if (
            not isinstance(raw, PsycopgConnection)
            or raw.autocommit
            or connection.get_isolation_level() != "READ COMMITTED"
        ):
            raise ValueError("migrations require non-autocommit READ COMMITTED")
        connection.execute(text("SELECT set_config('lock_timeout', '250ms', true)"))
        connection.execute(text("SELECT set_config('statement_timeout', '5000ms', true)"))
        if (
            connection.execute(text("SELECT pg_try_advisory_xact_lock(:key)"), {"key": LOCK}).scalar_one()
            is not True
        ):
            raise BusyMigration("another cooperating migration holds the database lock")
        cfg.attributes["connection"] = connection
        yield cfg
