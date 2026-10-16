from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from academy_ingestion_service.models import Base

metadata = MetaData()
for table in Base.metadata.sorted_tables:
    table.to_metadata(metadata)


def word() -> Text:
    return Text(collation="C")


outbox = Table(
    "delivery_outbox",
    metadata,
    Column("namespace", word(), primary_key=True),
    Column("id", word(), primary_key=True),
    Column("revision", Integer, primary_key=True),
    Column("value", Integer, nullable=False),
    Column("acknowledged", Boolean, nullable=False, server_default=text("false")),
    CheckConstraint("value BETWEEN 0 AND 1000000"),
    ForeignKeyConstraint(
        ["namespace", "id", "revision"], ["feed_record.namespace", "feed_record.id", "feed_record.revision"]
    ),
)
inbox = Table(
    "delivery_inbox",
    metadata,
    Column("namespace", word(), primary_key=True),
    Column("id", word(), primary_key=True),
    Column("revision", Integer, primary_key=True),
    Column("value", Integer, nullable=False),
    CheckConstraint("namespace ~ '^[a-z][a-z0-9-]{0,31}$'"),
    CheckConstraint("id ~ '^[a-z][a-z0-9-]{0,31}$'"),
    CheckConstraint("revision BETWEEN 1 AND 8"),
    CheckConstraint("value BETWEEN 0 AND 1000000"),
)
effect = Table(
    "delivery_effect",
    metadata,
    Column("namespace", word(), primary_key=True),
    Column("total", BigInteger, nullable=False),
    Column("applied", BigInteger, nullable=False),
    CheckConstraint("namespace ~ '^[a-z][a-z0-9-]{0,31}$'"),
    CheckConstraint("total >= 0"),
    CheckConstraint("applied > 0"),
)
policy = Table(
    "worker_policy",
    metadata,
    Column("namespace", word(), ForeignKey("feed_source.namespace"), primary_key=True),
    Column("lease_ms", Integer, nullable=False),
    Column("max_attempts", Integer, nullable=False),
    Column("delays_ms", ARRAY(Integer), nullable=False),
    CheckConstraint("lease_ms BETWEEN 100 AND 60000"),
    CheckConstraint("max_attempts BETWEEN 1 AND 8"),
    CheckConstraint("cardinality(delays_ms) = max_attempts - 1"),
    CheckConstraint("0 <= ALL(delays_ms) AND 60000 >= ALL(delays_ms)"),
)
job = Table(
    "delivery_job",
    metadata,
    Column("namespace", word(), ForeignKey("worker_policy.namespace"), primary_key=True),
    Column("id", word(), primary_key=True),
    Column("revision", Integer, primary_key=True),
    Column("generation", BigInteger, nullable=False, server_default=text("0")),
    Column("state", Text, nullable=False, server_default=text("'ready'")),
    Column("next_at", DateTime(timezone=True), nullable=False, server_default=text("clock_timestamp()")),
    Column("lease_until", DateTime(timezone=True)),
    Column("reason", Text),
    ForeignKeyConstraint(
        ["namespace", "id", "revision"],
        ["delivery_outbox.namespace", "delivery_outbox.id", "delivery_outbox.revision"],
    ),
    CheckConstraint("generation BETWEEN 0 AND 8"),
    CheckConstraint("state IN ('ready','leased','done','dead')"),
    CheckConstraint("reason IN ('retry','poison','exhausted')"),
    CheckConstraint("(state = 'leased') = (lease_until IS NOT NULL)"),
    CheckConstraint("state <> 'leased' OR generation > 0"),
)
Index(
    "delivery_job_ready",
    job.c.namespace,
    job.c.next_at,
    job.c.id,
    job.c.revision,
    postgresql_where=text("state='ready'"),
)
