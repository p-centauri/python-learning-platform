from academy_durable_outbox import Event


def encode(event: Event, *, version: int = 2) -> bytes:
    raise NotImplementedError("encode the supported exact version and stable fact")


def decode(payload: bytes, namespace: str, /) -> Event:
    raise NotImplementedError("validate bounded JSON, supported shape and authorized namespace")
