"""Error-to-text-key mapping for the UI layers."""

from __future__ import annotations

import pytest

from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.services.errors import (
    login_failure_text_key,
    text_key_for_exception,
)
from market_monitor_gui.texts import ru

pytestmark = pytest.mark.unit


def test_api_error_uses_its_text_key() -> None:
    exc = ApiError(ErrorKind.NETWORK)
    key = text_key_for_exception(exc)
    assert key == "ERR_NETWORK"
    assert ru.text_for(key) == ru.ERR_NETWORK


def test_auth_required_error_keeps_missing_secret_key() -> None:
    exc = ApiError(ErrorKind.UNAUTHORIZED, text_key="ERR_SECRET_REQUIRED")
    assert text_key_for_exception(exc) == "ERR_SECRET_REQUIRED"


def test_unknown_exception_maps_to_generic_key() -> None:
    assert text_key_for_exception(RuntimeError("boom")) == ru.ERR_UNEXPECTED


def test_login_failure_401_uses_login_failed_text() -> None:
    exc = ApiError(ErrorKind.UNAUTHORIZED, status_code=401)
    assert login_failure_text_key(exc) == ru.LOGIN_FAILED


def test_login_failure_network_keeps_network_text() -> None:
    exc = ApiError(ErrorKind.NETWORK)
    assert login_failure_text_key(exc) == "ERR_NETWORK"


def test_all_mapped_keys_are_registered() -> None:
    for kind in ErrorKind:
        assert text_key_for_exception(ApiError(kind)) in ru.TEXT_KEYS
