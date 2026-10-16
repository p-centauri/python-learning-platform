import asyncio

import pytest

from academy_async_feeds import Source


@pytest.fixture
def sources():
    return [Source("feed-a", "https://example.test/a"), Source("feed-b", "https://example.test/b")]


@pytest.fixture
def run_async():
    # A watchdog detects deadlocks; no test claims an exact wall-clock speed.
    def run(coroutine):
        return asyncio.run(asyncio.wait_for(coroutine, timeout=2))

    return run
