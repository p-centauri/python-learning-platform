"""Supplied pure validation and finite event vocabulary. No I/O during import."""
from collections.abc import Mapping
import json
import logging
import re
from psycopg2 import Error as PsycopgError
from academy_ingestion_service.database import url_from_dsn
from .contracts import ConfigurationError, Reason, Settings


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError()
        result[key] = value
    return result


def validate(dsn: object, tokens: object) -> Settings:
    try:
        if type(dsn) is not str or not 1 <= len(dsn) <= 1024:
            raise ConfigurationError()
        url_from_dsn(dsn)
        if type(tokens) is not dict or not 1 <= len(tokens) <= 8:
            raise ConfigurationError()
        copied: list[tuple[str, str]] = []
        for credential, namespace in tokens.items():
            if type(credential) is not str or re.fullmatch(r"[A-Za-z0-9_-]{16,64}", credential) is None:
                raise ConfigurationError()
            if type(namespace) is not str or re.fullmatch(r"[a-z][a-z0-9-]{0,31}", namespace) is None:
                raise ConfigurationError()
            copied.append((credential, namespace))
        return Settings(dsn, tuple(copied))
    except (ValueError, TypeError, PsycopgError):
        raise ConfigurationError() from None


def snapshot(environment: Mapping[str, str]) -> Settings:
    dsn = environment.get("ACADEMY_RELEASE_DSN")
    raw = environment.get("ACADEMY_RELEASE_TOKENS")
    if type(raw) is not str:
        raise ConfigurationError()
    try:
        length = len(raw.encode("utf-8"))
    except UnicodeError:
        raise ConfigurationError() from None
    if not 1 <= length <= 4096:
        raise ConfigurationError()
    try:
        tokens: object = json.loads(raw, object_pairs_hook=unique_object)
    except (ValueError, TypeError):
        raise ConfigurationError() from None
    return validate(dsn, tokens)


def revalidate(settings: Settings) -> Settings:
    if type(settings) is not Settings or type(settings.tokens) is not tuple:
        raise ConfigurationError()
    try:
        if any(type(pair) is not tuple or len(pair) != 2 for pair in settings.tokens):
            raise ConfigurationError()
        tokens = dict(settings.tokens)
        if len(tokens) != len(settings.tokens):
            raise ConfigurationError()
        return validate(settings.dsn, tokens)
    except (ValueError, TypeError):
        raise ConfigurationError() from None


def emit(event: str, reason: Reason) -> None:
    if event not in {"startup-ready", "startup-refused", "stopping", "disposed", "prepared", "checked", "rollback", "operation-refused"}:
        raise ValueError("invalid diagnostic event")
    logging.getLogger("academy_delivery_release").info(
        json.dumps({"event": event, "reason": reason.value}, sort_keys=True)
    )
