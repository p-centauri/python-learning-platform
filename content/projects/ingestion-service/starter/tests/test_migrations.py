from datetime import datetime
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from academy_ingestion_service import check_migrations, create_app, downgrade, upgrade
from test_contracts import TOKEN, request

pytestmark = pytest.mark.postgres


def test_upgrade_downgrade_reupgrade_preserves_key_value_rows(base_engine):
    engine = base_engine
    upgrade(engine, "service_001")
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO feed_source VALUES ('feed')"))
        conn.execute(text("INSERT INTO feed_record VALUES ('feed','a',1,5)"))
    upgrade(engine)
    check_migrations(engine)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT namespace,id,revision,value,ingested_at FROM feed_record")).one()
        assert (
            tuple(row[:4]) == ("feed", "a", 1, 5)
            and isinstance(row[4], datetime)
            and row[4].tzinfo is not None
        )
    downgrade(engine, "service_001")
    assert "ingested_at" not in {c["name"] for c in inspect(engine).get_columns("feed_record")}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT namespace,id,revision,value FROM feed_record")).one() == (
            "feed",
            "a",
            1,
            5,
        )
    upgrade(engine)
    check_migrations(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT namespace,id,revision,value FROM feed_record")).one() == (
            "feed",
            "a",
            1,
            5,
        )
    assert engine.pool.checkedout() == 0


def test_base_downgrade_is_explicitly_destructive_in_disposable_schema(base_engine):
    upgrade(base_engine)
    downgrade(base_engine, "base")
    assert set(inspect(base_engine).get_table_names()) == {"alembic_version"}
    upgrade(base_engine)
    check_migrations(base_engine)


def test_readiness_rejects_missing_or_old_schema(base_engine):
    app = create_app(base_engine, {TOKEN: "feed"})
    missing = request(app, "GET", "/ready", token=None)
    assert missing.status_code == 503 and missing.json() == {"detail": "storage operation failed"}
    upgrade(base_engine, "service_001")
    assert request(app, "GET", "/ready", token=None).status_code == 503
    upgrade(base_engine)
    assert request(app, "GET", "/ready", token=None).status_code == 200
    assert base_engine.pool.checkedout() == 0


@pytest.mark.parametrize(
    "query,params,code",
    [
        (
            "INSERT INTO feed_record(namespace,id,revision,value) VALUES (:ns,:id,:rev,:value)",
            {"ns": "missing", "id": "a", "rev": 1, "value": 5},
            "23503",
        ),
        (
            "INSERT INTO feed_record(namespace,id,revision,value) VALUES (:ns,:id,:rev,:value)",
            {"ns": "feed", "id": "a", "rev": 1, "value": -1},
            "23514",
        ),
        (
            "INSERT INTO feed_record(namespace,id,revision,value) VALUES (:ns,:id,:rev,:value)",
            {"ns": "feed", "id": "a", "rev": 1, "value": None},
            "23502",
        ),
        ("INSERT INTO feed_source VALUES (:ns)", {"ns": "feed"}, "23505"),
    ],
)
def test_migrated_database_enforces_direct_sql_constraints(engine, query, params, code):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO feed_source VALUES ('feed')"))
    with pytest.raises(IntegrityError) as error:
        with engine.begin() as conn:
            conn.execute(text(query), params)
    assert error.value.orig.pgcode == code
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM feed_record")).scalar_one() == 0
