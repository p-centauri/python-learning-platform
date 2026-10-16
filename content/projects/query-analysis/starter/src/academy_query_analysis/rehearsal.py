"""Supplied separate reporting schema and finite workload; disposable databases only."""
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import files
import json
import uuid
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import make_dsn, parse_dsn
from sqlalchemy import Engine, text
from academy_delivery_release.rehearsal import store as service_store
from academy_ingestion_service import make_engine
from academy_ingestion_service.database import url_from_dsn


@contextmanager
def store(dsn: str) -> Iterator[tuple[Engine, Engine, str]]:
    with service_store(dsn) as (private, source_engine, namespace):
        admin = psycopg2.connect(private, connect_timeout=5)
        report_schema = "queries_" + uuid.uuid4().hex
        query_engine = None
        try:
            with source_engine.connect() as connection:
                source_schema = connection.execute(text("SELECT current_schema()")).scalar_one()
            with admin, admin.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(report_schema)))
                template = files("academy_query_analysis").joinpath("annotation.sql").read_text()
                cursor.execute(sql.SQL(template).format(report=sql.Identifier(report_schema), source=sql.Identifier(source_schema)))
            values = parse_dsn(private)
            values["options"] = f"-csearch_path={report_schema},{source_schema}"
            query_engine = make_engine(url_from_dsn(make_dsn(**values)))
            yield source_engine, query_engine, namespace
        finally:
            if query_engine is not None:
                query_engine.dispose()
            admin.rollback()
            admin.autocommit = True
            try:
                with admin.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(report_schema)))
            finally:
                admin.close()


def note(engine: Engine, namespace: str, id: str, revision: int, note_id: str, body: dict[str, object]) -> None:
    # Fixture-only writes; caller has already configured an owned report/source search_path.
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO query_note VALUES (:ns,:id,:rev,:note,CAST(:body AS jsonb))"), {"ns": namespace, "id": id, "rev": revision, "note": note_id, "body": json.dumps(body)})


def workload(source: Engine, query: Engine, namespace: str) -> None:
    """40,000 revisions/notes, 10 rare kinds, 100 selective high values; no random seed."""
    with source.begin() as connection:
        connection.execute(text("INSERT INTO feed_source VALUES (:ns)"), {"ns": namespace})
        connection.execute(text("INSERT INTO feed_record(namespace,id,revision,value) SELECT :ns,'item-' || lpad(i::text,5,'0'),1,CASE WHEN i % 400 = 0 THEN 900000 + i / 400 ELSE i % 10000 END FROM generate_series(1,40000) AS i"), {"ns": namespace})
        connection.execute(text("ANALYZE feed_record"))
    with query.begin() as connection:
        connection.execute(text("INSERT INTO query_note SELECT namespace,id,revision,'meta',jsonb_build_object('kind',CASE WHEN value = 900001 OR id IN ('item-04000','item-08000','item-12000','item-16000','item-20000','item-24000','item-28000','item-32000','item-36000') THEN 'rare' ELSE 'common' END,'region','west') FROM feed_record WHERE namespace=:ns"), {"ns": namespace})
        connection.execute(text("ANALYZE query_note"))


def indexes(source: Engine, query: Engine, *, create: bool) -> None:
    """Explicit fixture experiment, outside read operations; restore source metadata afterwards."""
    with source.begin() as connection:
        connection.execute(text("CREATE INDEX query_value_cover ON feed_record(namespace,value,id,revision)" if create else "DROP INDEX query_value_cover"))
        connection.execute(text("ANALYZE feed_record"))
    with query.begin() as connection:
        connection.execute(text("CREATE INDEX query_note_body_gin ON query_note USING gin(body jsonb_path_ops)" if create else "DROP INDEX query_note_body_gin"))
        connection.execute(text("ANALYZE query_note"))
