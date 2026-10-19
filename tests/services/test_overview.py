"""G8: Overview use-case (dashboard summary + optional health)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.auth.session import SessionManager
from market_monitor_gui.db.cache import CacheKey, CacheStore, JsonValue
from market_monitor_gui.db.database import Database
from market_monitor_gui.services.overview import load_overview

pytestmark = pytest.mark.unit

ORIGIN = "https://api.test.example"

SUMMARY: JsonValue = {
    "groups_total": 5,
    "groups_enabled": 3,
    "products_total": 100,
    "products_active": 80,
    "products_missing": 20,
    "pending_deliveries": 4,
    "failed_deliveries": 1,
    "worker_status": "ok",
    "worker_last_heartbeat_at": None,
    "last_successful_scan_at": "2026-10-18T10:00:00+00:00",
}

HEALTH: JsonValue = {
    "worker": {
        "worker_id": "w1",
        "status": "running",
        "is_alive": True,
        "last_heartbeat_at": "2026-10-18T10:00:00+00:00",
        "last_scan_started_at": None,
        "last_scan_finished_at": None,
        "last_successful_scan_at": None,
        "last_error_at": None,
        "details": None,
    },
    "latest_scan_run": {
        "id": 1,
        "status": "success",
        "started_at": "2026-10-18T09:00:00+00:00",
        "finished_at": None,
        "groups_total": 5,
        "groups_success": 5,
        "groups_failed": 0,
        "products_seen": 100,
        "new_products": 2,
        "price_drops": 3,
        "errors": 0,
        "duration_ms": 1000,
        "error_summary": None,
    },
    "enabled_groups": 3,
    "total_groups": 5,
    "products_count": 100,
    "pending_deliveries": 4,
    "failed_deliveries": 1,
    "last_successful_scan_at": "2026-10-18T10:00:00+00:00",
}


def _handler(
    *,
    summary: httpx.Response | Exception | None = None,
    health: httpx.Response | Exception | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/dashboard/summary"):
            if isinstance(summary, Exception):
                raise summary
            return summary if summary is not None else httpx.Response(200, json=SUMMARY)
        if request.url.path.endswith("/health/status"):
            if isinstance(health, Exception):
                raise health
            return health if health is not None else httpx.Response(200, json=HEALTH)
        return httpx.Response(404, json={"detail": "not found"})

    return handler


def _setup(
    tmp_path: Path, handler: Callable[[httpx.Request], httpx.Response]
) -> tuple[SessionManager, ApiClient, CacheStore]:
    api = ApiClient.create(ORIGIN, transport=httpx.MockTransport(handler))
    session = SessionManager(api, secret_provider=lambda: "dummy")
    cache = CacheStore(Database(tmp_path / "state.db"))
    return session, api, cache


def test_loads_summary_and_health(tmp_path: Path) -> None:
    session, api, cache = _setup(tmp_path, _handler())
    data = load_overview(session, api, cache)
    assert data.groups_total == 5
    assert data.groups_enabled == 3
    assert data.products_total == 100
    assert data.failed_deliveries == 1
    assert data.worker_alive is True
    assert data.latest_scan_status == "success"
    assert data.from_cache is False


def test_health_failure_does_not_block_cards(tmp_path: Path) -> None:
    session, api, cache = _setup(tmp_path, _handler(health=httpx.Response(500)))
    data = load_overview(session, api, cache)
    assert data.groups_total == 5
    assert data.latest_scan_status is None
    assert data.worker_alive is None
    assert data.from_cache is False


def test_caches_summary_on_success(tmp_path: Path) -> None:
    session, api, cache = _setup(tmp_path, _handler())
    load_overview(session, api, cache)
    entry = cache.load(ORIGIN, CacheKey.DASHBOARD_SUMMARY.value)
    assert entry is not None
    assert isinstance(entry.payload, dict)
    assert entry.payload["groups_total"] == 5


def test_falls_back_to_cache_on_network_error(tmp_path: Path) -> None:
    session, api, cache = _setup(tmp_path, _handler(summary=httpx.ConnectError("boom")))
    cache.set_json(ORIGIN, CacheKey.DASHBOARD_SUMMARY.value, SUMMARY)
    data = load_overview(session, api, cache)
    assert data.from_cache is True
    assert data.cached_at is not None
    assert data.groups_total == 5
    assert data.latest_scan_status is None


def test_raises_network_error_without_cache(tmp_path: Path) -> None:
    session, api, cache = _setup(tmp_path, _handler(summary=httpx.ConnectError("boom")))
    with pytest.raises(ApiError) as excinfo:
        load_overview(session, api, cache)
    assert excinfo.value.kind is ErrorKind.NETWORK


def test_server_error_does_not_use_cache(tmp_path: Path) -> None:
    session, api, cache = _setup(tmp_path, _handler(summary=httpx.Response(500)))
    cache.set_json(ORIGIN, CacheKey.DASHBOARD_SUMMARY.value, SUMMARY)
    with pytest.raises(ApiError) as excinfo:
        load_overview(session, api, cache)
    assert excinfo.value.kind is ErrorKind.SERVER
