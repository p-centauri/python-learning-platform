from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SourceRow(Base):
    __tablename__ = "feed_source"
    __table_args__ = (CheckConstraint("namespace ~ '^[a-z][a-z0-9-]{0,31}$'", name="source_namespace"),)
    namespace: Mapped[str] = mapped_column(Text(collation="C"), primary_key=True)


class RecordRow(Base):
    __tablename__ = "feed_record"
    __table_args__ = (
        CheckConstraint("id ~ '^[a-z][a-z0-9-]{0,31}$'", name="record_id"),
        CheckConstraint("revision BETWEEN 1 AND 8", name="record_revision"),
        CheckConstraint("value BETWEEN 0 AND 1000000", name="record_value"),
    )
    namespace: Mapped[str] = mapped_column(
        Text(collation="C"), ForeignKey("feed_source.namespace"), primary_key=True
    )
    id: Mapped[str] = mapped_column(Text(collation="C"), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
