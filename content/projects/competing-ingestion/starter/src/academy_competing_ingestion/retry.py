from collections.abc import Callable, Sequence
import time
from sqlalchemy import Engine
from academy_ingestion_service import Datum
from academy_ingestion_service import ingest as ingest
from .contracts import Decision, Delivery, RetryPolicy
from .contracts import owned_session as owned_session
from .contracts import require_engine as require_engine


def classify_sqlstate(code: str | None, /) -> Decision:
    """Classify documented SQLSTATE, never exception wording. See README."""
    raise NotImplementedError("implement SQLSTATE classification")


def retry_ingest(
    engine: Engine,
    namespace: str,
    rows: Sequence[Datum],
    /,
    *,
    policy: RetryPolicy = RetryPolicy(),
    sleep: Callable[[float], None] = time.sleep,
) -> Delivery:
    """Own a fresh Session per bounded whole-transaction attempt; never replay unknown outcomes."""
    raise NotImplementedError("implement bounded transaction attempts")
