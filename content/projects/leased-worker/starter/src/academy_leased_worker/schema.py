from importlib.resources import files
from sqlalchemy import Engine, text
from academy_competing_ingestion.contracts import require_engine


def install(engine: Engine) -> None:
    require_engine(engine)
    with engine.begin() as connection:
        if connection.execute(text("SELECT to_regclass('delivery_outbox')")).scalar_one() is None:
            raise ValueError("install the completed outbox extension first")
        connection.exec_driver_sql(files("academy_leased_worker").joinpath("schema.sql").read_text())
