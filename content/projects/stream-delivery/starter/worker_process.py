import os
import sys
from threading import Event as StopEvent
from sqlalchemy import event
from psycopg2.extensions import connection as PGConnection
from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from academy_ingestion_service import make_engine
from academy_ingestion_service.database import url_from_dsn
from academy_durable_outbox import Accepted, Event
from academy_leased_worker import Policy, run
from academy_stream_delivery import RedisBroker, deliver, encode


def main() -> None:
    stage, namespace = sys.argv[1:]
    engine = make_engine(url_from_dsn(os.environ["ACADEMY_STREAM_DSN"]))
    name = os.environ["ACADEMY_STREAM_CHILD"]

    @event.listens_for(engine, "connect")
    def tag(connection: PGConnection, _: object) -> None:
        with connection.cursor() as cursor:
            cursor.execute("SET application_name = %s", (name,))
        connection.commit()

    client = Redis.from_url(
        os.environ["ACADEMY_BROKER_URL"],
        decode_responses=False,
        client_name=name,
        socket_timeout=2,
        socket_connect_timeout=2,
        retry=Retry(NoBackoff(), 0),
    )
    try:
        if stage == "after-append":
            broker = RedisBroker(client)

            def publishing(item: Event) -> Accepted:
                broker.append(namespace, encode(item))
                os._exit(91)

            run(engine, namespace, Policy(100, 3, (0, 0)), publishing, StopEvent())
        elif stage == "after-effect":

            class ExitBeforeAck(RedisBroker):
                def ack(self, namespace: str, group: str, id: bytes) -> bool:
                    os._exit(92)

            deliver(engine, ExitBeforeAck(client), namespace, "effects", "first")
        else:
            raise ValueError("unknown authored boundary")
    finally:
        client.close()
        engine.dispose()


if __name__ == "__main__":
    main()
