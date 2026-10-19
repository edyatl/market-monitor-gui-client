"""G9: Groups use-case (list with cache fallback + CRUD)."""

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
from market_monitor_gui.services.groups import (
    create_group,
    delete_group,
    load_groups,
    set_group_enabled,
    update_group,
)

pytestmark = pytest.mark.unit

ORIGIN = "https://api.test.example"

GROUP: JsonValue = {
    "id": 1,
    "name": "G1",
    "url": "https://shop.example/1",
    "enabled": True,
    "sort_order": 0,
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


def test_load_groups_success_and_cache(tmp_path: Path) -> None:
    session, api, cache, _ = _setup(tmp_path, lambda _r: httpx.Response(200, json=[GROUP]))
    data = load_groups(session, api, cache)
    assert data.from_cache is False
    assert len(data.groups) == 1
    assert data.groups[0].name == "G1"
    assert cache.load(ORIGIN, CacheKey.GROUPS.value) is not None


def test_load_groups_falls_back_to_cache(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    session, api, cache, _ = _setup(tmp_path, handler)
    cache.set_json(ORIGIN, CacheKey.GROUPS.value, [GROUP])
    data = load_groups(session, api, cache)
    assert data.from_cache is True
    assert data.cached_at is not None
    assert data.groups[0].id == 1


def test_load_groups_raises_without_cache(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    session, api, cache, _ = _setup(tmp_path, handler)
    with pytest.raises(ApiError) as excinfo:
        load_groups(session, api, cache)
    assert excinfo.value.kind is ErrorKind.NETWORK


def test_create_group_posts_expected_payload(tmp_path: Path) -> None:
    session, api, _cache, seen = _setup(tmp_path, lambda _r: httpx.Response(201, json=GROUP))
    created = create_group(session, api, name="G1", url="https://shop.example/1", enabled=True)
    assert created.id == 1
    request = seen[-1]
    assert request.method == "POST"
    assert request.url.path == "/api/v1/groups"
    assert _body(request) == {
        "name": "G1",
        "url": "https://shop.example/1",
        "enabled": True,
    }


def test_update_group_patches_expected_payload(tmp_path: Path) -> None:
    session, api, _cache, seen = _setup(tmp_path, lambda _r: httpx.Response(200, json=GROUP))
    update_group(session, api, 1, name="G1b", url="https://shop.example/2", enabled=False)
    request = seen[-1]
    assert request.method == "PATCH"
    assert request.url.path == "/api/v1/groups/1"
    assert _body(request) == {
        "name": "G1b",
        "url": "https://shop.example/2",
        "enabled": False,
    }


def test_set_group_enabled_sends_only_enabled(tmp_path: Path) -> None:
    session, api, _cache, seen = _setup(tmp_path, lambda _r: httpx.Response(200, json=GROUP))
    set_group_enabled(session, api, 1, enabled=False)
    request = seen[-1]
    assert request.method == "PATCH"
    assert request.url.path == "/api/v1/groups/1"
    assert _body(request) == {"enabled": False}


def test_delete_group_issues_delete(tmp_path: Path) -> None:
    session, api, _cache, seen = _setup(tmp_path, lambda _r: httpx.Response(204))
    delete_group(session, api, 7)
    request = seen[-1]
    assert request.method == "DELETE"
    assert request.url.path == "/api/v1/groups/7"


def test_delete_group_conflict_raises_conflict(tmp_path: Path) -> None:
    session, api, _cache, _ = _setup(
        tmp_path, lambda _r: httpx.Response(409, json={"detail": "in use"})
    )
    with pytest.raises(ApiError) as excinfo:
        delete_group(session, api, 7)
    assert excinfo.value.kind is ErrorKind.CONFLICT
