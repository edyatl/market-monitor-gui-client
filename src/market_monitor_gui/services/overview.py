"""Overview use-case: assemble the read-only dashboard view-model.

Runs the primary ``dashboard/summary`` read and an optional secondary
``health/status`` read through the :class:`SessionManager`, falling back to the
last-known cached summary when the network is unavailable. No invented fields: every
value comes from :class:`DashboardSummaryResponse` / :class:`HealthStatusResponse`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import ValidationError

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.dto import DashboardSummaryResponse, HealthStatusResponse
from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.auth.session import SessionManager
from market_monitor_gui.db.cache import CacheKey, CacheStore, JsonValue

_CACHE_FALLBACK_KINDS = (ErrorKind.NETWORK, ErrorKind.TIMEOUT)


@dataclass(frozen=True, slots=True)
class OverviewData:
    """Read-only Overview view-model built from live or cached API data."""

    groups_total: int
    groups_enabled: int
    products_total: int
    products_active: int
    products_missing: int
    pending_deliveries: int
    failed_deliveries: int
    worker_status: str | None
    worker_alive: bool | None
    last_successful_scan_at: datetime | None
    latest_scan_status: str | None
    from_cache: bool
    cached_at: datetime | None


def load_overview(session: SessionManager, api: ApiClient, cache: CacheStore) -> OverviewData:
    """Load the Overview data, using the cache only when the live read fails.

    The secondary ``health/status`` read is best-effort: its failure never blocks the
    primary cards.
    """
    try:
        summary = session.read(api.dashboard_summary)
    except ApiError as exc:
        if exc.kind not in _CACHE_FALLBACK_KINDS:
            raise
        entry = cache.load(api.origin, CacheKey.DASHBOARD_SUMMARY.value)
        if entry is None:
            raise
        cached = _parse_summary(entry.payload)
        if cached is None:
            raise
        return _build(cached, None, from_cache=True, cached_at=entry.fetched_at)

    cache.set_json(
        api.origin,
        CacheKey.DASHBOARD_SUMMARY.value,
        summary.model_dump(mode="json"),
    )
    health = _read_health(session, api)
    return _build(summary, health, from_cache=False, cached_at=None)


def _read_health(session: SessionManager, api: ApiClient) -> HealthStatusResponse | None:
    try:
        return session.read(api.health_status)
    except ApiError:
        return None


def _parse_summary(payload: JsonValue) -> DashboardSummaryResponse | None:
    try:
        return DashboardSummaryResponse.model_validate(payload)
    except ValidationError:
        return None


def _build(
    summary: DashboardSummaryResponse,
    health: HealthStatusResponse | None,
    *,
    from_cache: bool,
    cached_at: datetime | None,
) -> OverviewData:
    worker = health.worker if health is not None else None
    worker_status = summary.worker_status
    if worker_status is None and worker is not None:
        worker_status = worker.status
    latest_scan = health.latest_scan_run if health is not None else None
    return OverviewData(
        groups_total=summary.groups_total,
        groups_enabled=summary.groups_enabled,
        products_total=summary.products_total,
        products_active=summary.products_active,
        products_missing=summary.products_missing,
        pending_deliveries=summary.pending_deliveries,
        failed_deliveries=summary.failed_deliveries,
        worker_status=worker_status,
        worker_alive=worker.is_alive if worker is not None else None,
        last_successful_scan_at=summary.last_successful_scan_at,
        latest_scan_status=latest_scan.status if latest_scan is not None else None,
        from_cache=from_cache,
        cached_at=cached_at,
    )
