from importlib.resources import files
from sqlalchemy import Engine, text
from academy_competing_ingestion.contracts import require_engine


def install(engine: Engine) -> None:
    """Explicit one-time teaching DDL; never an import/request migration."""
    require_engine(engine)
    with engine.begin() as connection:
        if connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() != "service_002":
            raise ValueError("complete the prior service_002 schema first")
        connection.exec_driver_sql(files("academy_durable_outbox").joinpath("schema.sql").read_text())
