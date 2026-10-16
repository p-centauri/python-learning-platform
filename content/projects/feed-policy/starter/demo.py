from collections.abc import Iterable
from dataclasses import dataclass
import json
import logging

from academy_feed_policy import Reading, Report, apply_policy, logged_report, make_selector, parse_selector


@dataclass(frozen=True)
class ExampleReading:
    id: str
    value: int


def report(records: Iterable[Reading], /) -> Report:
    count = total = 0
    for record in records:
        count += 1
        total += record.value
    return {"count": count, "total": total}


def main() -> None:
    prefix, minimum = parse_selector("api:10")
    selector = make_selector(prefix=prefix, minimum=minimum)
    # The application configures handlers. The library does not call basicConfig.
    logger = logging.getLogger("academy_feed_policy.demo")
    reporter = logged_report(report, logger=logger, source_id="demo-feed")
    rows = [ExampleReading("api-fast", 5), ExampleReading("api-slow", 20), ExampleReading("worker", 30)]
    print(json.dumps(apply_policy(rows, selector=selector, reporter=reporter), sort_keys=True))


if __name__ == "__main__":
    main()
