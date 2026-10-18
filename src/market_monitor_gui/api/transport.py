"""HTTP transport construction for the API client.

One shared :class:`httpx.Client` is used for connection reuse and HTTP/2. TLS
verification is always on (``certifi`` bundle in packaged builds) and must never be
disabled. Timeouts are explicit for connect/read/write/pool so a hung request ends
in an error state instead of blocking forever.

The session cookie lives in the client's in-memory cookie jar and is never persisted.
"""

from __future__ import annotations

import ssl
from dataclasses import dataclass

import certifi
import httpx

from market_monitor_gui import __version__
from market_monitor_gui.config.urls import API_PREFIX

_USER_AGENT = f"MarketMonitorGUI/{__version__}"
_ACCEPT = "application/json, application/problem+json"


@dataclass(frozen=True, slots=True)
class TransportConfig:
    """Explicit timeouts and pool limits for the shared client."""

    connect_timeout: float = 5.0
    read_timeout: float = 10.0
    write_timeout: float = 10.0
    pool_timeout: float = 5.0
    max_connections: int = 10
    max_keepalive_connections: int = 5
    keepalive_expiry: float = 30.0
    http2: bool = True


def build_timeout(config: TransportConfig) -> httpx.Timeout:
    return httpx.Timeout(
        connect=config.connect_timeout,
        read=config.read_timeout,
        write=config.write_timeout,
        pool=config.pool_timeout,
    )


def build_limits(config: TransportConfig) -> httpx.Limits:
    return httpx.Limits(
        max_connections=config.max_connections,
        max_keepalive_connections=config.max_keepalive_connections,
        keepalive_expiry=config.keepalive_expiry,
    )


def default_verify() -> ssl.SSLContext:
    """Return the default TLS context using the ``certifi`` CA bundle."""
    return ssl.create_default_context(cafile=certifi.where())


def build_client(
    origin: str,
    config: TransportConfig | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
    verify: bool | str | ssl.SSLContext | None = None,
) -> httpx.Client:
    """Create the shared API client rooted at ``{origin}/api/v1/``.

    Args:
        origin: normalized API origin (scheme + host + optional port).
        config: timeouts/limits; defaults are used when omitted.
        transport: injectable transport for tests (``httpx.MockTransport``).
        verify: TLS verification setting; defaults to a ``certifi``-backed context
            and must not be set to ``False``.
    """
    effective = config if config is not None else TransportConfig()
    return httpx.Client(
        base_url=f"{origin}{API_PREFIX}/",
        http2=effective.http2,
        verify=default_verify() if verify is None else verify,
        timeout=build_timeout(effective),
        limits=build_limits(effective),
        follow_redirects=False,
        headers={"Accept": _ACCEPT, "User-Agent": _USER_AGENT},
        transport=transport,
    )
