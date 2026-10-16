"""Authored POSIX worker fixture; never import this module to install signal handlers."""

import json
import os
import signal
import sys
from dataclasses import asdict
from threading import Event as StopEvent
from sqlalchemy import event
from psycopg2.extensions import connection as PGConnection
from academy_ingestion_service import make_engine
from academy_ingestion_service.database import url_from_dsn
from academy_durable_outbox import Accepted, Event, consume
from academy_leased_worker import Policy, claim, run


def main() -> None:
    stage, namespace = sys.argv[1:]
    engine = make_engine(url_from_dsn(os.environ["ACADEMY_WORKER_DSN"]))
    name = os.environ["ACADEMY_WORKER_CHILD"]

    @event.listens_for(engine, "connect")
    def tag(connection: PGConnection, _: object) -> None:
        with connection.cursor() as cursor:
            cursor.execute("SET application_name = %s", (name,))
        connection.commit()

    try:
        if stage in ("after-claim", "after-accept"):
            lease = claim(engine, namespace, Policy(100, 3, (0, 0)))
            assert lease is not None
            if stage == "after-accept":
                consume(engine, lease.event)
            os._exit(81 if stage == "after-claim" else 82)
        if stage != "graceful":
            raise ValueError("unknown authored boundary")
        stop = StopEvent()

        def request_stop(signum: int, frame: object) -> None:
            stop.set()

        previous = signal.signal(signal.SIGTERM, request_stop)
        try:

            def publishing(item: Event) -> Accepted:
                # Parent sends SIGTERM only after observing this actual admission.
                print(json.dumps({"admitted": list(item.key)}), flush=True)
                if not stop.wait(5):
                    raise RuntimeError("the owned parent did not request shutdown")
                return consume(engine, item)

            result = run(engine, namespace, Policy(10000, 3, (0, 0)), publishing, stop)
            print(json.dumps({"report": asdict(result)}), flush=True)
        finally:
            signal.signal(signal.SIGTERM, previous)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
