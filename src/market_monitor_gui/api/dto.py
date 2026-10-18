"""Request/response DTOs mirroring ``docs/API_CONTRACT.md``.

Field names match the API exactly (notably ``price_drop_threshold_percent``).
Models ignore unknown fields so additive server changes do not break the client.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_MODEL_CONFIG = ConfigDict(extra="ignore", frozen=True)


class AppLoginRequest(BaseModel):
    model_config = _MODEL_CONFIG

    client_secret: str


class AppLoginResponse(BaseModel):
    model_config = _MODEL_CONFIG

    authenticated: bool
    expires_in: int


class AuthCheckResponse(BaseModel):
    model_config = _MODEL_CONFIG

    authenticated: bool


class LiveResponse(BaseModel):
    model_config = _MODEL_CONFIG

    status: str


class ReadyResponse(BaseModel):
    model_config = _MODEL_CONFIG

    status: str
    database: str


class GroupCreateRequest(BaseModel):
    model_config = _MODEL_CONFIG

    name: str
    url: str
    enabled: bool | None = None


class GroupPatchRequest(BaseModel):
    model_config = _MODEL_CONFIG

    name: str | None = None
    url: str | None = None
    enabled: bool | None = None
    sort_order: int | None = None


class GroupResponse(BaseModel):
    model_config = _MODEL_CONFIG

    id: int
    name: str
    url: str
    enabled: bool
    sort_order: int
    created_at: str
    updated_at: str


class FilterCreateRequest(BaseModel):
    model_config = _MODEL_CONFIG

    phrase: str


class FilterResponse(BaseModel):
    model_config = _MODEL_CONFIG

    id: int
    phrase: str
    normalized_phrase: str
    enabled: bool
    created_at: str
    updated_at: str


class SettingsPatchRequest(BaseModel):
    """PATCH body. The range is an input hint only; the server is authoritative."""

    model_config = _MODEL_CONFIG

    price_drop_threshold_percent: float | None = Field(default=None, ge=0.1, le=100)


class SettingsResponse(BaseModel):
    model_config = _MODEL_CONFIG

    price_drop_threshold_percent: float


class WorkerHealthSummary(BaseModel):
    model_config = _MODEL_CONFIG

    worker_id: str
    status: str
    is_alive: bool
    last_heartbeat_at: str
    last_scan_started_at: datetime | None = None
    last_scan_finished_at: datetime | None = None
    last_successful_scan_at: datetime | None = None
    last_error_at: datetime | None = None
    details: dict[str, Any] | None = None


class LatestScanRunSummary(BaseModel):
    model_config = _MODEL_CONFIG

    id: int | None = None
    status: str
    started_at: str
    finished_at: datetime | None = None
    groups_total: int = 0
    groups_success: int = 0
    groups_failed: int = 0
    products_seen: int = 0
    new_products: int = 0
    price_drops: int = 0
    errors: int = 0
    duration_ms: int | None = None
    error_summary: str | None = None


class HealthStatusResponse(BaseModel):
    model_config = _MODEL_CONFIG

    worker: WorkerHealthSummary | None = None
    latest_scan_run: LatestScanRunSummary | None = None
    enabled_groups: int = 0
    total_groups: int = 0
    products_count: int = 0
    pending_deliveries: int = 0
    failed_deliveries: int = 0
    last_successful_scan_at: datetime | None = None


class DashboardSummaryResponse(BaseModel):
    model_config = _MODEL_CONFIG

    groups_total: int = 0
    groups_enabled: int = 0
    products_total: int = 0
    products_active: int = 0
    products_missing: int = 0
    pending_deliveries: int = 0
    failed_deliveries: int = 0
    worker_status: str | None = None
    worker_last_heartbeat_at: datetime | None = None
    last_successful_scan_at: datetime | None = None
