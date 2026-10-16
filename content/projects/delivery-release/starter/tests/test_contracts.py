import json
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from academy_delivery_release import ConfigurationError, Reason, Settings, assess, create_release, load_settings
from academy_delivery_release.support import emit

TOKEN = "private_token_123456"
DSN = "host=127.0.0.1 dbname=disposable user=lab password=never-log-this"


def environment():
    return {"ACADEMY_RELEASE_DSN": DSN, "ACADEMY_RELEASE_TOKENS": json.dumps({TOKEN: "feed"})}


@pytest.mark.parametrize("key,value", [
    ("ACADEMY_RELEASE_DSN", ""),
    ("ACADEMY_RELEASE_DSN", "host=localhost"),
    ("ACADEMY_RELEASE_DSN", "host=" + "x" * 1025),
    ("ACADEMY_RELEASE_DSN", "host=x dbname=x user=x connect_timeout=9"),
    ("ACADEMY_RELEASE_TOKENS", "{}"),
    ("ACADEMY_RELEASE_TOKENS", "[]"),
    ("ACADEMY_RELEASE_TOKENS", '{"short":"feed"}'),
    ("ACADEMY_RELEASE_TOKENS", '{"private_token_123456":true}'),
    ("ACADEMY_RELEASE_TOKENS", '{"private_token_123456":"feed","private_token_123456":"other"}'),
    ("ACADEMY_RELEASE_TOKENS", "x" * 4097),
])
def test_invalid_private_settings_have_generic_error(key, value):
    values = environment()
    values[key] = value
    with pytest.raises(ConfigurationError) as caught:
        load_settings(values)
    assert str(caught.value) == "invalid release configuration"
    assert caught.value.__cause__ is None


def test_missing_configuration_has_no_default_credentials():
    with pytest.raises(ConfigurationError):
        load_settings({})


def test_configuration_snapshot_and_repr_do_not_leak():
    values = environment()
    configured = load_settings(values)
    values["ACADEMY_RELEASE_TOKENS"] = "{}"
    assert configured.tokens == ((TOKEN, "feed"),)
    assert TOKEN not in repr(configured) and DSN not in repr(configured)


def test_tampered_configuration_rejected_before_engine_allocation():
    settings = Settings(DSN, ((TOKEN, "feed"),))
    object.__setattr__(settings, "tokens", ((TOKEN, "bad namespace"),))
    with patch("academy_delivery_release.operations.make_engine") as factory:
        with pytest.raises(ConfigurationError):
            create_release(settings)
        factory.assert_not_called()


def test_wrong_dialect_is_programming_error_not_ready():
    engine = create_engine("sqlite://")
    try:
        with pytest.raises(ValueError):
            assess(engine)
    finally:
        engine.dispose()


def test_diagnostic_vocabulary_rejects_arbitrary_error(caplog):
    with caplog.at_level("INFO", logger="academy_delivery_release"):
        emit("checked", Reason.SCHEMA_HEAD)
    assert json.loads(caplog.records[-1].message) == {"event": "checked", "reason": "schema-head"}
    with pytest.raises(ValueError):
        emit("password=secret", Reason.READY)
