"""Guarded actual PostgreSQL query and plan evidence on caller's disposable database."""
import argparse
from dataclasses import asdict
from importlib.metadata import version
import json
import os
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from academy_ingestion_service import Datum, ingest
from academy_delivery_schema import check, inspect_state
from academy_delivery_release import assess
from academy_query_analysis import Filter, PlanQuery, explain, history, search, summarize
from academy_query_analysis.rehearsal import indexes, note, store, workload
from academy_query_analysis.support import read, resource


def observe() -> dict[str, object]:
    dsn = os.environ["ACADEMY_QUERY_DSN"]
    with store(dsn) as (source, query, namespace):
        with Session(source) as session:
            receipt = ingest(session, namespace, [Datum("a",1,0),Datum("a",3,7),Datum("a",8,2),Datum("b",1,2)])
        note(query,namespace,"a",1,"first",{"kind":"alert"})
        note(query,namespace,"a",1,"second",{"kind":"alert"})
        note(query,namespace,"a",8,"last",{"kind":"alert","region":None})
        note(query,namespace,"b",1,"last",{"kind":"alert","region":""})
        with source.connect() as connection:
            before = tuple(connection.execute(text("SELECT * FROM feed_record ORDER BY id,revision")).all())
        result = summarize(query,namespace)
        assert result is not None
        joined = asdict(result)
        joined.pop("namespace")
        revisions = [asdict(row) for row in history(query,namespace,"a")]
        matched = [asdict(row) for row in search(query,namespace,Filter('{"kind":"alert"}'))]
        null_matches = [asdict(row) for row in search(query,namespace,Filter('{"region":null}'))]
        with source.connect() as connection:
            unchanged = tuple(connection.execute(text("SELECT * FROM feed_record ORDER BY id,revision")).all()) == before
        check(source)
        compatible = assess(source).ready
        assert isinstance(query.pool,QueuePool)
        functional = dict(inserted=receipt.inserted,summary=joined,history=revisions,matches=matched,json_null_matches=null_matches,facts_unchanged=unchanged,source_ready=compatible,query_pool_checked_out=query.pool.checkedout())
    with store(dsn) as (source,query,namespace):
        workload(source,query,namespace)
        parameters = {"namespace":namespace,"minimum":900000,"maximum":900100,"limit":32,"filter":'{"kind":"rare"}'}
        with read(query) as connection:
            before_range = tuple(connection.execute(text(resource("range.sql")),parameters).all())
            before_notes = tuple(connection.execute(text(resource("notes.sql")),parameters).all())
        baseline = dict(range=asdict(explain(query,PlanQuery.RANGE,namespace)),notes=asdict(explain(query,PlanQuery.NOTES,namespace)))
        indexes(source,query,create=True)
        try:
            indexed = dict(range=asdict(explain(query,PlanQuery.RANGE,namespace)),notes=asdict(explain(query,PlanQuery.NOTES,namespace)),wide_range=asdict(explain(query,PlanQuery.RANGE,namespace,minimum=0,maximum=1000000)))
            with read(query) as connection:
                range_equal = tuple(connection.execute(text(resource("range.sql")),parameters).all()) == before_range
                notes_equal = tuple(connection.execute(text(resource("notes.sql")),parameters).all()) == before_notes
                counts = [connection.execute(text("SELECT count(*) FROM " + name)).scalar_one() for name in ("feed_record","query_note")]
                server = int(connection.execute(text("SHOW server_version_num")).scalar_one())
        finally:
            indexes(source,query,create=False)
        check(source)
        assert isinstance(query.pool,QueuePool) and isinstance(source.pool,QueuePool)
        return dict(schema="2026.10-query-analysis-v1",functional=functional,head=list(inspect_state(source).revisions),server_version=server,
                    workload=dict(records=counts[0],notes=counts[1],rare_notes=len(before_notes),selective_returned=len(before_range),limit=32,analyzed=True),
                    equivalent=dict(range=range_equal,notes=notes_equal),baseline=baseline,indexed=indexed,
                    checked_out=dict(source=source.pool.checkedout(),query=query.pool.checkedout()),
                    versions={name:version(name) for name in ("academy-query-analysis-lab","academy-delivery-release-lab","SQLAlchemy","psycopg2-binary")})


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=observe()
    output=json.dumps(report,indent=2)+"\n"
    args.output.write_text(output)
    print(output,end="")


if __name__ == "__main__":
    main()
