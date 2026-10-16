from collections.abc import Sequence
from sqlalchemy import Engine
from academy_ingestion_service import Datum
from .contracts import Reconciliation, RetryPolicy


def reconcile(
    engine: Engine, namespace: str, rows: Sequence[Datum], /, *, policy: RetryPolicy = RetryPolicy()
) -> Reconciliation:
    """Read only full-key/value facts for one namespace; absence is not rollback proof."""
    raise NotImplementedError("implement scoped reconciliation")
