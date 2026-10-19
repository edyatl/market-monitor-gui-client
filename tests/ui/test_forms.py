"""Tk-free form validation and outcome mapping for dialogs."""

from __future__ import annotations

import pytest

from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.config.urls import DEFAULT_API_BASE_URL
from market_monitor_gui.texts import ru
from market_monitor_gui.ui.forms import (
    custom_origin_warning,
    login_error_text,
    validate_group_form,
    validate_origin_input,
    validate_secret_input,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://api.example.org", "https://api.example.org"),
        ("https://api.example.org/api/v1", "https://api.example.org"),
        ("https://api.example.org/", "https://api.example.org"),
    ],
)
def test_https_origin_is_normalized_without_warning(raw: str, expected: str) -> None:
    result = validate_origin_input(raw)
    assert result.origin == expected
    assert result.error is None
    assert result.warning is None


@pytest.mark.parametrize("raw", ["http://localhost:8000", "http://127.0.0.1", "http://[::1]:8000"])
def test_loopback_http_is_allowed_without_warning(raw: str) -> None:
    result = validate_origin_input(raw)
    assert result.error is None
    assert result.warning is None
    assert result.origin is not None and result.origin.startswith("http://")


def test_non_loopback_http_warns_but_is_accepted() -> None:
    result = validate_origin_input("http://api.example.org")
    assert result.origin == "http://api.example.org"
    assert result.error is None
    assert result.warning == ru.CONN_WRN_NOT_HTTPS


def test_invalid_origin_reports_error_key() -> None:
    result = validate_origin_input("not a url")
    assert result.origin is None
    assert result.error == ru.CONN_ORIGIN_INVALID


def test_custom_origin_warning_only_for_non_default() -> None:
    assert custom_origin_warning(DEFAULT_API_BASE_URL) is None
    assert custom_origin_warning("https://api.example.org") == ru.CONN_CUSTOM_ORIGIN_WARNING


def test_validate_secret_input_rejects_blank_only() -> None:
    assert validate_secret_input("   ") == ru.ERR_SECRET_REQUIRED
    assert validate_secret_input("") == ru.ERR_SECRET_REQUIRED
    assert validate_secret_input("s3cret") is None


def test_login_error_text_uses_login_failed_on_401() -> None:
    assert login_error_text(ApiError(ErrorKind.UNAUTHORIZED)) == ru.LOGIN_FAILED


def test_validate_group_form_accepts_and_trims() -> None:
    result = validate_group_form("  G1  ", "  https://shop.example/1  ", True)
    assert result.error is None
    assert result.values is not None
    assert result.values.name == "G1"
    assert result.values.url == "https://shop.example/1"
    assert result.values.enabled is True


def test_validate_group_form_requires_name() -> None:
    result = validate_group_form("   ", "https://shop.example/1", True)
    assert result.values is None
    assert result.error == ru.GROUP_NAME_REQUIRED


def test_validate_group_form_rejects_overlong_name() -> None:
    result = validate_group_form("a" * 201, "https://shop.example/1", True)
    assert result.values is None
    assert result.error == ru.GROUP_NAME_TOO_LONG


def test_validate_group_form_requires_url() -> None:
    result = validate_group_form("G1", "   ", True)
    assert result.values is None
    assert result.error == ru.GROUP_URL_REQUIRED


@pytest.mark.parametrize("url", ["shop.example", "ftp://shop.example", "www.example"])
def test_validate_group_form_rejects_non_http_url(url: str) -> None:
    result = validate_group_form("G1", url, True)
    assert result.values is None
    assert result.error == ru.GROUP_URL_INVALID
