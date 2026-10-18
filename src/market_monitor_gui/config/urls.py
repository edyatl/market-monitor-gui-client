"""API origin normalization and URL construction.

The client stores a single **origin**: scheme + host + optional port, with no path.
Accepted inputs are normalized so both of these work without operator edits:

- ``https://api.market-resale-signal.xubi.org``
- ``https://api.market-resale-signal.xubi.org/api/v1`` (trailing ``/api/v1[/]`` stripped)

URLs are built from the normalized origin:

- API calls: ``{origin}/api/v1/<path>``
- Liveness: ``{origin}/health/live`` (public, deliberately outside ``/api/v1``)

Connection settings in the screens batch must reuse these helpers instead of
building URLs by hand.
"""

from __future__ import annotations

from typing import Final
from urllib.parse import urlsplit

DEFAULT_API_BASE_URL: Final[str] = "https://api.market-resale-signal.xubi.org"
API_PREFIX: Final[str] = "/api/v1"
LIVE_PATH: Final[str] = "/health/live"

_ALLOWED_SCHEMES: Final[frozenset[str]] = frozenset({"http", "https"})

_LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset({"localhost", "127.0.0.1", "::1"})


def normalize_api_origin(raw: str) -> str:
    """Return the canonical origin (scheme + host + optional port) for ``raw``.

    Strips surrounding whitespace, any path, a trailing ``/api/v1`` suffix, query,
    and fragment. Scheme and host are lower-cased.

    Raises:
        ValueError: when the value is empty, has no host, uses a non-HTTP scheme, or
            embeds credentials.
    """
    value = raw.strip()
    if not value:
        raise ValueError("API base URL is empty")

    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"invalid API base URL: {raw!r}") from exc

    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise ValueError(f"API base URL must use http or https: {raw!r}")
    if not host:
        raise ValueError(f"API base URL has no host: {raw!r}")
    if parsed.username or parsed.password:
        raise ValueError("API base URL must not contain credentials")

    host_part = f"[{host}]" if ":" in host else host
    netloc = host_part if port is None else f"{host_part}:{port}"
    return f"{parsed.scheme.lower()}://{netloc}"


def api_url(origin: str, path: str) -> str:
    """Build an absolute ``/api/v1`` URL for ``path`` (leading slash optional)."""
    return f"{origin}{API_PREFIX}/{path.lstrip('/')}"


def live_url(origin: str) -> str:
    """Build the absolute public liveness URL for ``origin``."""
    return f"{origin}{LIVE_PATH}"


def is_default_origin(origin: str) -> bool:
    """Return True when ``origin`` resolves to the built-in production origin."""
    try:
        return normalize_api_origin(origin) == normalize_api_origin(DEFAULT_API_BASE_URL)
    except ValueError:
        return False


def is_loopback_origin(origin: str) -> bool:
    """Return True when ``origin`` points at the local machine (dev exception)."""
    try:
        host = urlsplit(origin).hostname
    except ValueError:
        return False
    if not host:
        return False
    return host.lower() in _LOOPBACK_HOSTS
