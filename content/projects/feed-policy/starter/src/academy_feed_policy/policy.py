from collections.abc import Iterable
import logging

from .contracts import Reading, Report, Reporter, Selector


def parse_selector(spec: str) -> tuple[str, int]:
    """Parse a complete bounded ASCII prefix:minimum rule. See README."""
    raise NotImplementedError("Implement the explicit rule grammar")


def make_selector(*, prefix: str, minimum: int) -> Selector:
    """Validate once and return an independent predicate closure."""
    raise NotImplementedError("Implement the selector factory")


def logged_report(reporter: Reporter, *, logger: logging.Logger, source_id: str) -> Reporter:
    """Add safe outcome events, preserving results, failures and metadata."""
    raise NotImplementedError("Implement the reporting decorator")


def apply_policy(records: Iterable[Reading], *, selector: Selector, reporter: Reporter) -> Report:
    """Borrow records; let the reporter consume the filtered iterator once."""
    selected = (record for record in records if selector(record))
    return reporter(selected)
