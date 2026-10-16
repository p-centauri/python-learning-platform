from sqlalchemy import Engine
from .contracts import Broker, Result


def deliver(
    engine: Engine,
    broker: Broker,
    namespace: str,
    group: str,
    consumer: str,
    /,
    *,
    recover: bool = False,
    idle_ms: int = 100,
    cursor: bytes = b"0-0",
) -> Result:
    raise NotImplementedError("validate one delivery, commit the inbox/effect, then acknowledge")
