"""Trusted disposable crash fixture. This process deliberately exits without cleanup."""

import argparse
import os
from typing import NoReturn, Any
from sqlalchemy import event as sql_event
from sqlalchemy.pool import ConnectionPoolEntry
from psycopg2.extensions import connection as PgConnection
from academy_ingestion_service import Datum, make_engine
from academy_ingestion_service.database import url_from_dsn
from academy_durable_outbox import Accepted, Event, consume, publish_one, record


def main() -> NoReturn:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage", choices=["before-record-commit", "after-record-commit", "after-consume-commit"]
    )
    parser.add_argument("namespace")
    args = parser.parse_args()
    engine = make_engine(url_from_dsn(os.environ["ACADEMY_OUTBOX_DSN"]))

    def tag(connection: PgConnection, entry: ConnectionPoolEntry) -> None:
        with connection.cursor() as cursor:
            cursor.execute("SET application_name = %s", (os.environ["ACADEMY_OUTBOX_CHILD"],))
        connection.commit()

    sql_event.listen(engine, "connect", tag)
    if args.stage == "before-record-commit":

        def stop(*values: Any) -> None:
            statement = values[2]
            if "INSERT INTO delivery_outbox" in statement:
                os._exit(71)

        sql_event.listen(engine, "after_cursor_execute", stop)
        record(engine, args.namespace, [Datum("a", 1, 7)])
    elif args.stage == "after-record-commit":
        record(engine, args.namespace, [Datum("a", 1, 7)])
        os._exit(72)
    else:

        def publish(item: Event) -> Accepted:
            consume(engine, item)
            os._exit(73)

        publish_one(engine, args.namespace, publish)
    raise AssertionError("configured crash boundary was not reached")


if __name__ == "__main__":
    main()
