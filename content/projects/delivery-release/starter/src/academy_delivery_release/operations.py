from collections.abc import Mapping
from sqlalchemy import Engine
from .contracts import Readiness, Release, Settings


def load_settings(environment: Mapping[str, str]) -> Settings:
    """Validate explicit private settings and copy credentials; no connection/default secrets."""
    raise NotImplementedError("Implement immutable validated configuration")


def assess(engine: Engine) -> Readiness:
    """Fresh read-only delivery_004 head/column check; finite reasons, released Session/connection."""
    raise NotImplementedError("Implement scoped release readiness")


def create_release(settings: Settings) -> Release:
    """Own one engine/lifespan; mount unchanged service behind readiness/admission and dispose once."""
    raise NotImplementedError("Implement compatible release ownership")
