"""G11: Filters (exclusions) use-case (list with cache fallback + add/delete)."""

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
from market_monitor_gui.services.filters import create_filter, delete_filter, load_filters

pytestmark = pytest.mark.unit

ORIGIN = "https://api.test.example"

FILTER: JsonValue = {
    "id": 1,
    "phrase": "no spam",
    "normalized_phrase": "no spam",
    "enabled": True,
    "created_at": "2026-10-18T10:00:00+00:00",
    "updated_at": "2026-10-18T10:00:00+00:00",
}


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


def test_load_filters_success_and_cache(tmp_path: Path) -> None:
    session, api, cache, _ = _setup(tmp_path, lambda _r: httpx.Response(200, json=[FILTER]))
    data = load_filters(session, api, cache)
    assert data.from_cache is False
    assert len(data.filters) == 1
    assert data.filters[0].phrase == "no spam"
    assert data.filters[0].normalized_phrase == "no spam"
    assert cache.load(ORIGIN, CacheKey.FILTERS.value) is not None


def test_load_filters_falls_back_to_cache(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    session, api, cache, _ = _setup(tmp_path, handler)
    cache.set_json(ORIGIN, CacheKey.FILTERS.value, [FILTER])
    data = load_filters(session, api, cache)
    assert data.from_cache is True
    assert data.cached_at is not None
    assert data.filters[0].id == 1


def test_load_filters_raises_without_cache(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    session, api, cache, _ = _setup(tmp_path, handler)
    with pytest.raises(ApiError) as excinfo:
        load_filters(session, api, cache)
    assert excinfo.value.kind is ErrorKind.NETWORK


def test_create_filter_posts_phrase_only(tmp_path: Path) -> None:
    session, api, _cache, seen = _setup(tmp_path, lambda _r: httpx.Response(201, json=FILTER))
    created = create_filter(session, api, phrase="no spam")
    assert created.id == 1
    request = seen[-1]
    assert request.method == "POST"
    assert request.url.path == "/api/v1/filters"
    # No `enabled` (or any other field) is ever sent on create.
    assert _body(request) == {"phrase": "no spam"}


def test_delete_filter_issues_delete(tmp_path: Path) -> None:
    session, api, _cache, seen = _setup(tmp_path, lambda _r: httpx.Response(204))
    delete_filter(session, api, 7)
    request = seen[-1]
    assert request.method == "DELETE"
    assert request.url.path == "/api/v1/filters/7"


def test_delete_filter_not_found_maps_to_not_found(tmp_path: Path) -> None:
    session, api, _cache, _ = _setup(
        tmp_path, lambda _r: httpx.Response(404, json={"detail": "missing"})
    )
    with pytest.raises(ApiError) as excinfo:
        delete_filter(session, api, 7)
    assert excinfo.value.kind is ErrorKind.NOT_FOUND
