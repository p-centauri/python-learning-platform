from collections.abc import Sequence
from sqlalchemy.orm import Session
from .contracts import Cursor, Datum, Page, Receipt


def ingest(session: Session, namespace: str, rows: Sequence[Datum], /) -> Receipt:
    """Own one new transaction on an idle borrowed Session; preserve append-only facts."""
    raise NotImplementedError("implement validated atomic ingestion and exact duplicate classification")


def read_page(session: Session, namespace: str, /, *, limit: int = 16, after: Cursor | None = None) -> Page:
    """Own a read transaction; authorize outside, filter/order/bound inside; no count-total claim."""
    raise NotImplementedError("implement scoped keyset pagination with one extra observation")
