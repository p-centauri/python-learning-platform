from dataclasses import dataclass
import logging

import pytest


@dataclass(frozen=True)
class SampleReading:
    id: str
    value: int


@pytest.fixture
def readings():
    return [SampleReading("api-fast", 5), SampleReading("api-slow", 20), SampleReading("worker", 30)]


@pytest.fixture
def logger():
    # Restore configuration even when a test assertion fails.
    instance = logging.getLogger("academy_feed_policy.tests")
    old_level = instance.level
    instance.setLevel(logging.INFO)
    try:
        yield instance
    finally:
        instance.setLevel(old_level)
