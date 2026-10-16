from collections.abc import Iterable
from academy_ingestion_service import Datum, Page
from .contracts import Analysis, Item


def decode_page(payload: object) -> Page:
    """Copy exact old service items/cursor envelope, preserving 0..1m values and stable ordering."""
    raise NotImplementedError("Implement the typed public service boundary")


def prepare(namespace: str, rows: Iterable[Datum]) -> tuple[Item, ...]:
    """Borrow <=256 rows; detect all full-key conflicts, choose latest per id, sort <=64 Items."""
    raise NotImplementedError("Implement immutable latest-revision preparation")


def analyse(items: tuple[Item, ...], requests: tuple[int, ...], *, cached: bool = False) -> Analysis:
    """Return ordered equivalent fingerprints with a fresh single-caller eight-entry cache."""
    raise NotImplementedError("Implement compatible baseline and bounded-cache reporting")
