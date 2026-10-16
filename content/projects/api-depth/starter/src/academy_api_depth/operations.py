from sqlalchemy import Engine
from academy_ingestion_service import Datum


def matches(header: str | None, etag: str) -> bool:
    """Bounded If-None-Match: wildcard or weak comparison of quoted tags; invalid lists fail."""
    raise NotImplementedError("Implement conditional GET comparison")


def verify(
    secret: bytes, namespace: str, delivery: str, timestamp: str, signature: str, body: bytes, *, now: int
) -> None:
    """Authenticate exact raw bytes plus fixed version/route/delivery/time; +/-300 seconds."""
    raise NotImplementedError("Implement signed webhook authentication")


def accept(engine: Engine, namespace: str, delivery: str, digest: str, datum: Datum) -> bool:
    """Commit receipt and reading together. Return True for same-body delivery duplicate."""
    raise NotImplementedError("Implement atomic local delivery acceptance")
