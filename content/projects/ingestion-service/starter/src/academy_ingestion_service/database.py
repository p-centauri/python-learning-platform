from importlib.resources import files
from io import StringIO
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, URL, create_engine
from psycopg2.extensions import parse_dsn

HEAD = "service_002"


def make_engine(url: URL) -> Engine:
    if url.drivername != "postgresql+psycopg2":
        raise ValueError("the lab requires PostgreSQL through Psycopg 2")
    return create_engine(
        url,
        isolation_level="READ COMMITTED",
        pool_size=2,
        max_overflow=0,
        pool_timeout=5,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


def migration_config() -> Config:
    cfg = Config(stdout=StringIO())
    cfg.set_main_option("script_location", str(files("academy_ingestion_service").joinpath("migrations")))
    return cfg


def upgrade(engine: Engine, revision: str = "head") -> None:
    cfg = migration_config()
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, revision)


def downgrade(engine: Engine, revision: str) -> None:
    cfg = migration_config()
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.downgrade(cfg, revision)


def check_migrations(engine: Engine) -> None:
    cfg = migration_config()
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.check(cfg)


def url_from_dsn(dsn: str) -> URL:
    values = parse_dsn(dsn)
    if not {"host", "dbname", "user"} <= values.keys() or values.keys() - {
        "host",
        "port",
        "dbname",
        "user",
        "password",
        "options",
    }:
        raise ValueError("use explicit local host/database/user and supported local DSN options")
    query = {"options": values["options"]} if "options" in values else {}
    return URL.create(
        "postgresql+psycopg2",
        username=values.get("user"),
        password=values.get("password"),
        host=values.get("host"),
        port=int(values.get("port", "5432")),
        database=values.get("dbname"),
        query=query,
    )
