from collections.abc import Iterable
from functools import wraps
import logging
import re

from .contracts import Reading, Report, Reporter, RuleError, Selector


def parse_selector(spec: str) -> tuple[str, int]:
    if not isinstance(spec, str) or len(spec) > 22:
        raise RuleError("Invalid selector")
    match = re.fullmatch(r"([a-z][a-z0-9-]{0,15}):(0|[1-9][0-9]{0,4})", spec)
    if match is None:
        raise RuleError("Invalid selector")
    prefix, raw_minimum = match.groups()
    minimum = int(raw_minimum)
    if minimum > 60000:
        raise RuleError("Invalid selector")
    return prefix, minimum


def make_selector(*, prefix: str, minimum: int) -> Selector:
    if (
        not isinstance(prefix, str)
        or len(prefix) > 16
        or re.fullmatch(r"[a-z][a-z0-9-]{0,15}", prefix) is None
        or type(minimum) is not int
        or not 0 <= minimum <= 60000
    ):
        raise RuleError("Invalid selector settings")

    def selected(record: Reading) -> bool:
        return record.id.startswith(prefix) and record.value >= minimum

    return selected


def logged_report(reporter: Reporter, *, logger: logging.Logger, source_id: str) -> Reporter:
    if (
        not isinstance(source_id, str)
        or len(source_id) > 32
        or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", source_id) is None
    ):
        raise RuleError("Invalid source label")

    @wraps(reporter)
    def observed(records: Iterable[Reading], /) -> Report:
        logger.info("feed_report_started", extra={"source_id": source_id})
        try:
            result = reporter(records)
        except Exception:
            logger.warning("feed_report_failed", extra={"source_id": source_id})
            raise
        logger.info(
            "feed_report_succeeded", extra={"source_id": source_id, "record_count": result["count"]}
        )
        return result

    return observed


def apply_policy(records: Iterable[Reading], *, selector: Selector, reporter: Reporter) -> Report:
    selected = (record for record in records if selector(record))
    return reporter(selected)
