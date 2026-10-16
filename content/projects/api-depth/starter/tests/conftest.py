import os
import pytest
from academy_api_depth.rehearsal import store


@pytest.fixture
def live():
    dsn = os.environ.get("ACADEMY_API_TEST_DSN")
    if not dsn:
        pytest.skip("requires an explicit disposable PostgreSQL store")
    with store(dsn) as owned:
        yield owned
