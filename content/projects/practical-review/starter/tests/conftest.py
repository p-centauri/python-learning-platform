import os
import pytest
from academy_practical_review.rehearsal import store


@pytest.fixture
def live():
    dsn = os.environ.get("ACADEMY_PRACTICAL_DSN")
    if not dsn:
        pytest.skip("requires explicit disposable PostgreSQL")
    with store(dsn) as engine:
        yield engine
