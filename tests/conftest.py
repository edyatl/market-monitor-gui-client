"""Shared pytest fixtures and global guards."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx
import pytest


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Fail fast if a test attempts real HTTP.

    ``httpx.MockTransport`` (and ``respx``) do not go through the real transports,
    so mocking still works while an accidental live request raises immediately.
    """

    def _blocked(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("network access is not allowed in unit tests")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", _blocked)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", _blocked)
    yield


@pytest.fixture(autouse=True)
def _clean_app_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove ambient app env vars so settings tests are deterministic."""
    for name in ("APP_SECRET", "API_APP_KEY", "API_BASE_URL", "APP_ENV"):
        monkeypatch.delenv(name, raising=False)
    yield
