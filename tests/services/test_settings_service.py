"""G10: Settings use-case (read with cache fallback + PATCH)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.auth.session import SessionManager
from market_monitor_gui.db.cache import CacheKey, CacheStore, JsonValue
from market_monitor_gui.db.database import Database
from market_monitor_gui.services.settings import load_settings, save_settings

pytestmark = pytest.mark.unit

ORIGIN = "https://api.test.example"

SETTINGS: JsonValue = {"price_drop_threshold_percent": 7.5}


def _setup(
    tmp_path: Path, handler: Callable[[httpx.Request], httpx.Response]
) -> tuple[SessionManager, ApiClient, CacheStore, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    api = ApiClient.create(ORIGIN, transport=httpx.MockTransport(recording))
    session = SessionManager(api, secret_provider=lambda: "dummy")
    cache = CacheStore(Database(tmp_path / "state.db"))
    return session, api, cache, seen


def _body(request: httpx.Request) -> dict[str, object]:
    parsed: object = json.loads(request.content)
    assert isinstance(parsed, dict)
    return parsed


def test_load_settings_success_and_cache(tmp_path: Path) -> None:
    session, api, cache, _ = _setup(tmp_path, lambda _r: httpx.Response(200, json=SETTINGS))
    data = load_settings(session, api, cache)
    assert data.from_cache is False
    assert data.price_drop_threshold_percent == 7.5
    assert cache.load(ORIGIN, CacheKey.SETTINGS.value) is not None


def test_load_settings_falls_back_to_cache(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    session, api, cache, _ = _setup(tmp_path, handler)
    cache.set_json(ORIGIN, CacheKey.SETTINGS.value, SETTINGS)
    data = load_settings(session, api, cache)
    assert data.from_cache is True
    assert data.cached_at is not None
    assert data.price_drop_threshold_percent == 7.5


def test_load_settings_raises_without_cache(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    session, api, cache, _ = _setup(tmp_path, handler)
    with pytest.raises(ApiError) as excinfo:
        load_settings(session, api, cache)
    assert excinfo.value.kind is ErrorKind.NETWORK


def test_save_settings_patches_expected_payload(tmp_path: Path) -> None:
    session, api, _cache, seen = _setup(tmp_path, lambda _r: httpx.Response(200, json=SETTINGS))
    saved = save_settings(session, api, _cache, price_drop_threshold_percent=7.5)
    assert saved.price_drop_threshold_percent == 7.5
    request = seen[-1]
    assert request.method == "PATCH"
    assert request.url.path == "/api/v1/settings"
    assert _body(request) == {"price_drop_threshold_percent": 7.5}


def test_save_settings_updates_cache_from_response(tmp_path: Path) -> None:
    session, api, cache, _ = _setup(tmp_path, lambda _r: httpx.Response(200, json=SETTINGS))
    save_settings(session, api, cache, price_drop_threshold_percent=7.5)
    entry = cache.load(ORIGIN, CacheKey.SETTINGS.value)
    assert entry is not None
    assert isinstance(entry.payload, dict)
    assert entry.payload["price_drop_threshold_percent"] == 7.5


def test_save_settings_rejects_out_of_range_locally(tmp_path: Path) -> None:
    session, api, cache, seen = _setup(tmp_path, lambda _r: httpx.Response(200, json=SETTINGS))
    with pytest.raises(ApiError) as excinfo:
        save_settings(session, api, cache, price_drop_threshold_percent=0.05)
    assert excinfo.value.kind is ErrorKind.VALIDATION
    assert seen == []  # no request is made for an invalid value


def test_save_settings_maps_422_to_validation(tmp_path: Path) -> None:
    session, api, cache, _ = _setup(
        tmp_path, lambda _r: httpx.Response(422, json={"detail": "bad"})
    )
    with pytest.raises(ApiError) as excinfo:
        save_settings(session, api, cache, price_drop_threshold_percent=7.5)
    assert excinfo.value.kind is ErrorKind.VALIDATION
