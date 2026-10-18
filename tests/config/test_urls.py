"""G3: API origin normalization and URL construction."""

from __future__ import annotations

import pytest

from market_monitor_gui.config.urls import (
    API_PREFIX,
    DEFAULT_API_BASE_URL,
    api_url,
    is_default_origin,
    live_url,
    normalize_api_origin,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://api.market-resale-signal.xubi.org", DEFAULT_API_BASE_URL),
        ("https://api.market-resale-signal.xubi.org/", DEFAULT_API_BASE_URL),
        ("https://api.market-resale-signal.xubi.org/api/v1", DEFAULT_API_BASE_URL),
        ("https://api.market-resale-signal.xubi.org/api/v1/", DEFAULT_API_BASE_URL),
        ("  https://api.market-resale-signal.xubi.org/api/v1/  ", DEFAULT_API_BASE_URL),
        ("HTTPS://API.MARKET-RESALE-SIGNAL.XUBI.ORG", DEFAULT_API_BASE_URL),
        ("http://localhost:8000/api/v1", "http://localhost:8000"),
        ("http://localhost:8000", "http://localhost:8000"),
        ("https://host.example/some/path", "https://host.example"),
        ("https://host.example/api/v1?x=1#frag", "https://host.example"),
    ],
)
def test_normalize_accepted_inputs(raw: str, expected: str) -> None:
    assert normalize_api_origin(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "api.example.com",
        "ftp://api.example.com",
        "https://",
        "https://user:pass@api.example.com",
        "not a url",
    ],
)
def test_normalize_rejects_invalid_inputs(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_api_origin(raw)


def test_api_prefix_is_versioned_and_liveness_is_outside_it() -> None:
    assert API_PREFIX == "/api/v1"
    assert not live_url("https://h.example").startswith("https://h.example/api/v1")


def test_api_url_joins_path() -> None:
    assert (
        api_url("https://h.example", "auth/app-login") == "https://h.example/api/v1/auth/app-login"
    )
    assert api_url("https://h.example", "/groups/1") == "https://h.example/api/v1/groups/1"


def test_live_url() -> None:
    assert live_url("https://h.example") == "https://h.example/health/live"


def test_is_default_origin() -> None:
    assert is_default_origin(DEFAULT_API_BASE_URL)
    assert is_default_origin(DEFAULT_API_BASE_URL + "/api/v1/")
    assert not is_default_origin("http://localhost:8000")
    assert not is_default_origin("garbage")
