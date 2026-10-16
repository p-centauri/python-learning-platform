import os
import pytest
from academy_query_analysis.rehearsal import store


@pytest.fixture
def live():
    dsn = os.environ.get("ACADEMY_QUERY_DSN")
    if not dsn:
        pytest.skip("requires explicit disposable PostgreSQL configuration")
    with store(dsn) as owned:
        yield owned
