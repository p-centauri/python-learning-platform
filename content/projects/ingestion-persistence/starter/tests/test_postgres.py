import psycopg2
from psycopg2.extensions import (
    TRANSACTION_STATUS_IDLE,
    TRANSACTION_STATUS_INTRANS,
    TRANSACTION_STATUS_INERROR,
)
import pytest
from academy_ingestion_persistence import (
    BatchResult,
    ConflictingReading,
    Reading,
    load_namespace,
    persist_batch,
)

pytestmark = pytest.mark.postgres


def test_committed_batch_visible_on_second_connection(db):
    conn, other = db
    rows = [Reading("feed", "b", 1, 0), Reading("feed", "a", 2, 5), Reading("feed", "a", 1, 6)]
    assert persist_batch(conn, rows) == BatchResult(3, 3, 0)
    assert load_namespace(other, "feed") == (rows[2], rows[1], rows[0])
    assert conn.closed == other.closed == 0
    assert conn.get_transaction_status() == other.get_transaction_status() == TRANSACTION_STATUS_IDLE


def test_exact_duplicates_within_and_across_batches(db):
    conn, other = db
    row = Reading("feed", "a", 1, 0)
    assert persist_batch(conn, [row, row]) == BatchResult(2, 1, 1)
    assert persist_batch(conn, [row]) == BatchResult(1, 0, 1)
    assert load_namespace(other, "feed") == (row,)


def test_namespace_and_revision_are_separate_identities(db):
    conn, other = db
    rows = [Reading("feed", "a", 1, 5), Reading("other", "a", 1, 7), Reading("feed", "a", 2, 8)]
    assert persist_batch(conn, rows).inserted == 3
    assert len(load_namespace(other, "feed")) == 2
    assert len(load_namespace(other, "other")) == 1


def test_late_conflict_rolls_back_new_sources_and_rows(db):
    conn, other = db
    saved = Reading("feed", "a", 1, 5)
    persist_batch(conn, [saved])
    with pytest.raises(ConflictingReading):
        persist_batch(conn, [Reading("new-source", "x", 1, 4), Reading("feed", "a", 1, 6)])
    assert load_namespace(other, "new-source") == ()
    assert load_namespace(other, "feed") == (saved,)
    with other:
        with other.cursor() as cur:
            cur.execute("SELECT count(*) FROM feed_source WHERE namespace=%s", ("new-source",))
            assert cur.fetchone() == (0,)
    assert conn.get_transaction_status() == TRANSACTION_STATUS_IDLE
    assert persist_batch(conn, [Reading("new-source", "x", 1, 4)]).inserted == 1


def test_same_batch_conflict_rolls_back(db):
    conn, other = db
    with pytest.raises(ConflictingReading):
        persist_batch(conn, [Reading("feed", "a", 1, 1), Reading("feed", "a", 1, 2)])
    assert load_namespace(other, "feed") == ()


@pytest.mark.parametrize("mode", ["active", "failed", "autocommit", "isolation", "closed"])
def test_reject_caller_state_without_commit_rollback_or_close(db, mode):
    conn, other = db
    if mode in {"active", "failed"}:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO feed_source VALUES ('caller')")
            if mode == "failed":
                with pytest.raises(psycopg2.errors.DivisionByZero):
                    cur.execute("SELECT 1/0")
    elif mode == "autocommit":
        conn.autocommit = True
    elif mode == "isolation":
        conn.set_session(isolation_level="SERIALIZABLE")
    else:
        conn.close()
    for operation in [
        lambda: persist_batch(conn, [Reading("feed", "a", 1, 1)]),
        lambda: load_namespace(conn, "feed"),
    ]:
        with pytest.raises(ValueError):
            operation()
    if mode == "active":
        assert conn.get_transaction_status() == TRANSACTION_STATUS_INTRANS
        conn.commit()
        with other:
            with other.cursor() as cur:
                cur.execute("SELECT namespace FROM feed_source")
                assert cur.fetchall() == [("caller",)]
    elif mode == "failed":
        assert conn.get_transaction_status() == TRANSACTION_STATUS_INERROR


def test_driver_constraint_error_rolls_back_whole_batch(db):
    conn, other = db
    with conn:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE feed_record ADD CONSTRAINT exercise_failure CHECK (id <> 'bad')")
    with pytest.raises(psycopg2.errors.CheckViolation) as error:
        persist_batch(conn, [Reading("feed", "good", 1, 5), Reading("feed", "bad", 1, 6)])
    assert error.value.pgcode == "23514"
    assert load_namespace(other, "feed") == ()
    assert conn.get_transaction_status() == TRANSACTION_STATUS_IDLE and conn.closed == 0
    assert persist_batch(conn, [Reading("feed", "good", 1, 5)]).inserted == 1


@pytest.mark.parametrize(
    "statement,params,error_type,code",
    [
        (
            "INSERT INTO feed_record VALUES (%s,%s,%s,%s)",
            ("missing", "a", 1, 1),
            psycopg2.errors.ForeignKeyViolation,
            "23503",
        ),
        (
            "INSERT INTO feed_record VALUES (%s,%s,%s,%s)",
            ("feed", "a", 1, -1),
            psycopg2.errors.CheckViolation,
            "23514",
        ),
        (
            "INSERT INTO feed_record VALUES (%s,%s,%s,%s)",
            ("feed", "a", 9, 1),
            psycopg2.errors.CheckViolation,
            "23514",
        ),
        (
            "INSERT INTO feed_record VALUES (%s,%s,%s,%s)",
            ("feed", "a", 1, None),
            psycopg2.errors.NotNullViolation,
            "23502",
        ),
        ("INSERT INTO feed_source VALUES (%s)", ("Invalid",), psycopg2.errors.CheckViolation, "23514"),
        (
            "INSERT INTO feed_record VALUES (%s,%s,%s,%s)",
            ("feed", "a", 1, 1),
            psycopg2.errors.UniqueViolation,
            "23505",
        ),
    ],
)
def test_database_enforces_rules_without_python_validation(db, statement, params, error_type, code):
    conn, other = db
    saved = Reading("feed", "a", 1, 1)
    persist_batch(conn, [saved])
    with pytest.raises(error_type) as error:
        with conn:
            with conn.cursor() as cur:
                cur.execute(statement, params)
    assert error.value.pgcode == code
    assert load_namespace(other, "feed") == (saved,)
    assert conn.get_transaction_status() == TRANSACTION_STATUS_IDLE


def test_parameter_binding_keeps_punctuation_as_data(db):
    conn, _ = db
    text = "O'Reilly'); DROP TABLE feed_record; --"
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT %s::text", (text,))
            assert cur.fetchone() == (text,)
            cur.execute("SELECT count(*) FROM feed_record")
            assert cur.fetchone() == (0,)


def test_invalid_and_overflow_inputs_before_transaction(db):
    conn, other = db
    for rows in [[None], [Reading("feed", "a", 1, 0)] * 65]:
        with pytest.raises(ValueError):
            persist_batch(conn, rows)
        assert conn.get_transaction_status() == TRANSACTION_STATUS_IDLE
    assert load_namespace(other, "feed") == ()


def test_empty_batch_and_missing_namespace(db):
    conn, other = db
    assert persist_batch(conn, []) == BatchResult(0, 0, 0)
    assert load_namespace(other, "missing") == ()


def test_load_detects_namespace_overflow(db):
    conn, other = db
    persist_batch(conn, [Reading("feed", f"id-{n:02}", 1, n) for n in range(64)])
    assert len(load_namespace(other, "feed")) == 64
    persist_batch(conn, [Reading("feed", "last", 1, 1)])
    with pytest.raises(ValueError):
        load_namespace(other, "feed")
    assert other.get_transaction_status() == TRANSACTION_STATUS_IDLE and other.closed == 0


@pytest.mark.parametrize("namespace", ["", "feed'", None])
def test_invalid_read_before_transaction(db, namespace):
    conn, _ = db
    with pytest.raises(ValueError):
        load_namespace(conn, namespace)
    assert conn.get_transaction_status() == TRANSACTION_STATUS_IDLE


def test_iterator_failure_precedes_database_access(db):
    conn, other = db
    error = RuntimeError("source failed")

    def rows():
        yield Reading("feed", "a", 1, 5)
        raise error

    with pytest.raises(RuntimeError) as result:
        persist_batch(conn, rows())
    assert result.value is error
    assert conn.get_transaction_status() == TRANSACTION_STATUS_IDLE
    assert load_namespace(other, "feed") == ()
