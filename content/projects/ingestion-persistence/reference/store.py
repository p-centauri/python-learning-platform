from collections.abc import Iterable
from psycopg2.extensions import connection
from .contracts import BatchResult, ConflictingReading, Reading, field, require_idle


def snapshot_batch(source: Iterable[Reading], /) -> tuple[Reading, ...]:
    result: list[Reading] = []
    for reading in source:
        if len(result) == 64:
            raise ValueError("batch exceeds 64 readings")
        if type(reading) is not Reading:
            raise ValueError("expected exact Reading")
        # Frozen values describe ordinary code, not protection from object.__setattr__.
        Reading(reading.namespace, reading.id, reading.revision, reading.value)
        result.append(reading)
    return tuple(result)


def persist_batch(conn: connection, source: Iterable[Reading], /) -> BatchResult:
    batch = snapshot_batch(source)
    require_idle(conn)
    inserted = 0
    duplicates = 0
    with conn:
        with conn.cursor() as cursor:
            for reading in batch:
                key = (reading.namespace, reading.id, reading.revision)
                cursor.execute(
                    "INSERT INTO feed_source(namespace) VALUES (%s) ON CONFLICT (namespace) DO NOTHING",
                    (reading.namespace,),
                )
                cursor.execute(
                    "INSERT INTO feed_record(namespace, id, revision, value) VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (namespace, id, revision) DO NOTHING RETURNING value",
                    (*key, reading.value),
                )
                if cursor.fetchone() is not None:
                    inserted += 1
                else:
                    cursor.execute(
                        "SELECT value FROM feed_record WHERE namespace=%s AND id=%s AND revision=%s FOR SHARE",
                        key,
                    )
                    existing = cursor.fetchone()
                    if existing is None or existing[0] != reading.value:
                        raise ConflictingReading("identity conflicts with stored value")
                    duplicates += 1
    return BatchResult(len(batch), inserted, duplicates)


def load_namespace(conn: connection, namespace: str, /) -> tuple[Reading, ...]:
    field(namespace)
    require_idle(conn)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT namespace, id, revision, value FROM feed_record "
                'WHERE namespace=%s ORDER BY id COLLATE "C", revision LIMIT 65',
                (namespace,),
            )
            rows = cursor.fetchall()
            if len(rows) > 64:
                raise ValueError("namespace exceeds 64 readings")
            result = tuple(Reading(*row) for row in rows)
    return result
