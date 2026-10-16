from sqlalchemy import Engine
from academy_stream_delivery import RedisBroker
from .contracts import DeadJob, Pruned


def inspect_dead(engine: Engine, namespace: str, /, *, limit: int = 8) -> tuple[DeadJob, ...]:
    """Return at most limit current dead jobs in complete-key order; do not change state."""
    raise NotImplementedError("Implement bounded, scoped dead-job inspection")


def redrive(engine: Engine, job: DeadJob, /, *, approve: bool = False) -> bool:
    """Conditionally ready one exact poison job without resetting its saved generation/budget."""
    raise NotImplementedError("Implement guarded explicit redrive")


def prune(
    engine: Engine, broker: RedisBroker, namespace: str, id: bytes, /, *, allow_loss: bool = False
) -> Pruned:
    """Remove one eligible broker payload; retain all PostgreSQL identity/effect/job history."""
    raise NotImplementedError("Implement exact-id retention with supplied atomic broker guard")
