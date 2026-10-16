from collections.abc import Callable, Sequence
import re
import time
from sqlalchemy import Engine
from sqlalchemy.exc import DBAPIError
from academy_ingestion_service import Datum, ingest
from .contracts import (
    Decision,
    Delivery,
    RetryPolicy,
    RetryExhausted,
    UnknownOutcome,
    owned_session,
    snapshot,
    require_engine,
)


def classify_sqlstate(code: str | None, /) -> Decision:
    if code is None:
        return Decision.RECONCILE
    if type(code) is not str or re.fullmatch(r"[0-9A-Z]{5}", code, flags=re.ASCII) is None:
        raise ValueError("expected an exact five-character SQLSTATE or None")
    if code in {"40001", "40P01"}:
        return Decision.RETRY
    if code.startswith("08") or code in {"57P01", "57P02"}:
        return Decision.RECONCILE
    return Decision.STOP


def retry_ingest(
    engine: Engine,
    namespace: str,
    rows: Sequence[Datum],
    /,
    *,
    policy: RetryPolicy = RetryPolicy(),
    sleep: Callable[[float], None] = time.sleep,
) -> Delivery:
    batch = snapshot(namespace, rows)
    require_engine(engine)
    if type(policy) is not RetryPolicy:
        raise ValueError("expected exact RetryPolicy")
    RetryPolicy(policy.max_attempts, policy.lock_timeout_ms, policy.statement_timeout_ms, policy.delays)
    for attempt in range(1, policy.max_attempts + 1):
        try:
            with owned_session(engine, policy) as session:
                receipt = ingest(session, namespace, batch)
            return Delivery(receipt, attempt)
        except DBAPIError as error:
            code: str | None = getattr(error.orig, "pgcode", None)
            decision = classify_sqlstate(code)
            if decision is Decision.RECONCILE:
                raise UnknownOutcome(attempt) from error
            if decision is Decision.STOP:
                raise
            if attempt == policy.max_attempts:
                assert code is not None
                raise RetryExhausted(attempt, code) from error
        # Both rollback and Session closure finished before the borrowed sleeper runs.
        sleep(policy.delays[attempt - 1])
    raise AssertionError("unreachable attempt state")
