"""G4: shared client construction (HTTP/2, TLS, timeouts, limits, headers)."""

from __future__ import annotations

import ssl
from typing import Any

import httpx
import pytest

from market_monitor_gui.api.transport import (
    TransportConfig,
    build_client,
    build_limits,
    build_timeout,
)

pytestmark = pytest.mark.unit

ORIGIN = "https://api.test.example"


def _capture_client_kwargs(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}
    real_client = httpx.Client

    def fake_client(*args: Any, **kwargs: Any) -> httpx.Client:
        captured.update(kwargs)
        captured["_args"] = args
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", fake_client)
    return captured


def test_build_client_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _capture_client_kwargs(monkeypatch)
    client = build_client(ORIGIN)
    try:
        assert captured["base_url"] == f"{ORIGIN}/api/v1/"
        assert captured["http2"] is True
        assert captured["follow_redirects"] is False
        assert isinstance(captured["verify"], ssl.SSLContext)
        assert captured["verify"].verify_mode is ssl.CERT_REQUIRED
        timeout = captured["timeout"]
        assert isinstance(timeout, httpx.Timeout)
        assert timeout.connect == 5.0
        assert timeout.read == 10.0
        assert timeout.write == 10.0
        assert timeout.pool == 5.0
        limits = captured["limits"]
        assert isinstance(limits, httpx.Limits)
        assert limits.max_connections == 10
        assert client.base_url == httpx.URL(f"{ORIGIN}/api/v1/")
    finally:
        client.close()


def test_build_client_custom_config(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _capture_client_kwargs(monkeypatch)
    config = TransportConfig(
        connect_timeout=1.5,
        read_timeout=2.5,
        write_timeout=3.5,
        pool_timeout=4.5,
        max_connections=3,
        http2=False,
    )
    client = build_client(ORIGIN, config)
    try:
        assert captured["http2"] is False
        timeout = captured["timeout"]
        assert timeout.connect == 1.5
        assert timeout.read == 2.5
        assert timeout.write == 3.5
        assert timeout.pool == 4.5
        assert captured["limits"].max_connections == 3
    finally:
        client.close()


def test_accept_and_user_agent_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    client = build_client(ORIGIN)
    try:
        assert "application/problem+json" in client.headers["accept"]
        assert client.headers["user-agent"].startswith("MarketMonitorGUI/")
        assert "x-app-key" not in client.headers
    finally:
        client.close()


def test_build_timeout_and_limits_are_independent() -> None:
    config = TransportConfig()
    timeout = build_timeout(config)
    limits = build_limits(config)
    assert timeout.connect == config.connect_timeout
    assert limits.max_keepalive_connections == config.max_keepalive_connections


def test_verify_can_be_overridden_for_diagnostics_but_defaults_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_client_kwargs(monkeypatch)
    context = ssl.create_default_context()
    client = build_client(ORIGIN, verify=context)
    try:
        assert captured["verify"] is context
    finally:
        client.close()
