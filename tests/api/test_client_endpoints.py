"""G4: exact method/path for every client method, plus DTO parsing."""

from __future__ import annotations

import json

import httpx
import pytest

from market_monitor_gui.api.dto import (
    FilterCreateRequest,
    FilterResponse,
    GroupCreateRequest,
    GroupPatchRequest,
    GroupResponse,
    SettingsPatchRequest,
    SettingsResponse,
)

from .conftest import DEFAULT_ORIGIN, record_requests, urls

pytestmark = pytest.mark.unit

GROUP = {
    "id": 1,
    "name": "Группа A",
    "url": "https://market.example/search",
    "enabled": True,
    "sort_order": 0,
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-02T00:00:00",
}
FILTER = {
    "id": 7,
    "phrase": "  Чехол  ",
    "normalized_phrase": "чехол",
    "enabled": True,
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
}


def dispatcher(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    method = request.method
    if path == "/health/live":
        return httpx.Response(200, json={"status": "ok"})
    if path.endswith("/auth/app-login"):
        return httpx.Response(200, json={"authenticated": True, "expires_in": 1})
    if path.endswith("/auth/check"):
        return httpx.Response(200, json={"authenticated": True})
    if path.endswith("/health/ready"):
        return httpx.Response(200, json={"status": "ok", "database": "ok"})
    if path.endswith("/health/status"):
        return httpx.Response(200, json={"enabled_groups": 2, "total_groups": 3})
    if path.endswith("/dashboard/summary"):
        return httpx.Response(200, json={"groups_total": 3, "groups_enabled": 2})
    if path.endswith("/settings"):
        if method == "PATCH":
            return httpx.Response(200, json={"price_drop_threshold_percent": 7.5})
        return httpx.Response(200, json={"price_drop_threshold_percent": 5.0})
    if path.endswith("/groups"):
        if method == "POST":
            return httpx.Response(201, json=GROUP)
        return httpx.Response(200, json=[GROUP])
    if "/groups/" in path:
        if method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json=GROUP)
    if path.endswith("/filters"):
        if method == "POST":
            return httpx.Response(201, json=FILTER)
        return httpx.Response(200, json=[FILTER])
    if "/filters/" in path and method == "DELETE":
        return httpx.Response(204)
    return httpx.Response(404, json={"detail": "unhandled"})


@pytest.fixture
def client(make_client):
    seen, handler = record_requests(dispatcher)
    api = make_client(handler)
    api.requests_seen = seen  # type: ignore[attr-defined]
    return api


def test_live_uses_origin_root_not_api_prefix(client) -> None:
    fresh = client.live()
    assert fresh.status == "ok"
    assert urls(client.requests_seen) == [f"{DEFAULT_ORIGIN}/health/live"]


def test_health_endpoints(client) -> None:
    assert client.ready().database == "ok"
    assert client.health_status().enabled_groups == 2
    assert client.dashboard_summary().groups_total == 3
    assert urls(client.requests_seen) == [
        f"{DEFAULT_ORIGIN}/api/v1/health/ready",
        f"{DEFAULT_ORIGIN}/api/v1/health/status",
        f"{DEFAULT_ORIGIN}/api/v1/dashboard/summary",
    ]


def test_list_and_get_group(client) -> None:
    groups = client.list_groups()
    group = client.get_group(1)
    assert isinstance(groups[0], GroupResponse)
    assert groups[0].name == "Группа A"
    assert group.id == 1
    assert urls(client.requests_seen) == [
        f"{DEFAULT_ORIGIN}/api/v1/groups",
        f"{DEFAULT_ORIGIN}/api/v1/groups/1",
    ]


def test_create_group_omits_unset_enabled(client) -> None:
    created = client.create_group(GroupCreateRequest(name="n", url="u"))
    assert created.id == 1
    request = client.requests_seen[0]
    assert request.method == "POST"
    assert urls([request]) == [f"{DEFAULT_ORIGIN}/api/v1/groups"]
    assert json.loads(request.content) == {"name": "n", "url": "u"}


def test_create_group_includes_explicit_false(client) -> None:
    client.create_group(GroupCreateRequest(name="n", url="u", enabled=False))
    assert json.loads(client.requests_seen[0].content)["enabled"] is False


def test_patch_group_sends_only_set_fields_and_keeps_false(client) -> None:
    patched = client.patch_group(1, GroupPatchRequest(enabled=False))
    assert isinstance(patched, GroupResponse)
    request = client.requests_seen[0]
    assert request.method == "PATCH"
    assert json.loads(request.content) == {"enabled": False}


def test_delete_group_accepts_204(client) -> None:
    assert client.delete_group(1) is None
    request = client.requests_seen[0]
    assert request.method == "DELETE"
    assert urls([request]) == [f"{DEFAULT_ORIGIN}/api/v1/groups/1"]


def test_filters_round_trip(client) -> None:
    filters = client.list_filters()
    created = client.create_filter(FilterCreateRequest(phrase="  Чехол  "))
    assert isinstance(filters[0], FilterResponse)
    assert created.normalized_phrase == "чехол"
    assert client.delete_filter(7) is None
    assert [request.method for request in client.requests_seen] == ["GET", "POST", "DELETE"]
    assert urls(client.requests_seen) == [
        f"{DEFAULT_ORIGIN}/api/v1/filters",
        f"{DEFAULT_ORIGIN}/api/v1/filters",
        f"{DEFAULT_ORIGIN}/api/v1/filters/7",
    ]


def test_settings_get_and_patch(client) -> None:
    current = client.get_settings()
    updated = client.patch_settings(SettingsPatchRequest(price_drop_threshold_percent=7.5))
    assert isinstance(current, SettingsResponse)
    assert current.price_drop_threshold_percent == 5.0
    assert updated.price_drop_threshold_percent == 7.5
    assert json.loads(client.requests_seen[1].content) == {"price_drop_threshold_percent": 7.5}


def test_fractional_threshold_round_trips(client) -> None:
    client.patch_settings(SettingsPatchRequest(price_drop_threshold_percent=0.1))
    assert json.loads(client.requests_seen[0].content) == {"price_drop_threshold_percent": 0.1}
