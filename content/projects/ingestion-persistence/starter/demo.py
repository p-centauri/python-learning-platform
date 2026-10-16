"""Trusted local demo: unique temporary schema in an explicitly disposable database."""

import argparse
from dataclasses import asdict
from importlib.resources import files
from importlib.metadata import version
import json
import os
import uuid
import psycopg2
from psycopg2 import sql
from academy_ingestion_persistence import ConflictingReading, Reading, load_namespace, persist_batch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    dsn = os.environ.get("ACADEMY_PERSISTENCE_DSN")
    if not dsn:
        parser.error("set ACADEMY_PERSISTENCE_DSN to an explicitly disposable PostgreSQL database")
    schema = "demo_" + uuid.uuid4().hex
    conn = psycopg2.connect(dsn, connect_timeout=5)
    other = psycopg2.connect(dsn, connect_timeout=5)
    try:
        for client in (conn, other):
            client.set_session(isolation_level="READ COMMITTED", readonly=False, autocommit=False)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
                cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
                cur.execute(files("academy_ingestion_persistence").joinpath("schema.sql").read_text())
        with other:
            with other.cursor() as cur:
                cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        rows = [Reading("feed", "a", 1, 5), Reading("feed", "b", 1, 10)]
        first = persist_batch(conn, rows)
        repeat = persist_batch(conn, rows)
        visible = load_namespace(other, "feed")
        conflict = False
        try:
            persist_batch(conn, [Reading("new-feed", "x", 1, 9), Reading("feed", "a", 1, 99)])
        except ConflictingReading:
            conflict = True
        rolled_back = load_namespace(other, "new-feed") == ()
        sqlstates: dict[str, str | None] = {}
        probes = [
            ("foreign-key", "INSERT INTO feed_record VALUES (%s,%s,%s,%s)", ("missing", "x", 1, 5)),
            ("check", "INSERT INTO feed_record VALUES (%s,%s,%s,%s)", ("feed", "x", 1, -1)),
            ("not-null", "INSERT INTO feed_record VALUES (%s,%s,%s,%s)", ("feed", "x", 1, None)),
            ("unique", "INSERT INTO feed_record VALUES (%s,%s,%s,%s)", ("feed", "a", 1, 5)),
        ]
        for label, statement, params in probes:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(statement, params)
            except psycopg2.IntegrityError as error:
                sqlstates[label] = error.pgcode
        report = {
            "schema": "2026.10-persistence-v1",
            "server_version": conn.server_version,
            "driver": version("psycopg2-binary"),
            "first": asdict(first),
            "repeat": asdict(repeat),
            "second_connection_rows": [asdict(row) for row in visible],
            "late_conflict_rejected": conflict,
            "new_namespace_rolled_back": rolled_back,
            "sqlstates": sqlstates,
            "unchanged_after_failures": load_namespace(other, "feed") == visible,
            "connection_open": conn.closed == 0,
            "transaction_idle": conn.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_IDLE,
            "isolation": "READ COMMITTED",
            "automatic_retries": False,
        }
        encoded = json.dumps(report, indent=2) + "\n"
        if args.output:
            from pathlib import Path

            Path(args.output).write_text(encoded)
        print(encoded, end="")
    finally:
        conn.close()
        other.rollback()
        other.autocommit = True
        try:
            with other.cursor() as cur:
                cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        finally:
            other.close()


if __name__ == "__main__":
    main()
