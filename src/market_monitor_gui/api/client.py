"""Typed API client — the only layer that touches ``httpx`` and the cookie jar.

Every method is a single-shot request; retry/backoff and 401 re-login coordination
belong to the session manager. The shared client holds the session cookie in memory
only. No ``X-App-Key`` header is ever sent on normal API calls.

Paths are relative to the client's ``{origin}/api/v1/`` base; the public liveness
endpoint is called with an absolute URL because it lives outside ``/api/v1``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import httpx
from pydantic import TypeAdapter, ValidationError

from market_monitor_gui.api.dto import (
    AppLoginResponse,
    AuthCheckResponse,
    DashboardSummaryResponse,
    FilterCreateRequest,
    FilterResponse,
    GroupCreateRequest,
    GroupPatchRequest,
    GroupResponse,
    HealthStatusResponse,
    LiveResponse,
    ReadyResponse,
    SettingsPatchRequest,
    SettingsResponse,
)
from market_monitor_gui.api.errors import ApiError, ErrorKind, error_from_http
from market_monitor_gui.api.transport import TransportConfig, build_client
from market_monitor_gui.config.urls import live_url

_T = TypeVar("_T")

_GROUP_LIST: TypeAdapter[list[GroupResponse]] = TypeAdapter(list[GroupResponse])
_FILTER_LIST: TypeAdapter[list[FilterResponse]] = TypeAdapter(list[FilterResponse])

_OK = (200,)
_CREATED = (200, 201)
_NO_CONTENT = (200, 204)


class ApiClient:
    """Namespaced, typed wrappers over the Market Monitor control-plane API."""

    def __init__(self, client: httpx.Client, *, origin: str) -> None:
        self._client = client
        self._origin = origin

    @classmethod
    def create(
        cls,
        origin: str,
        *,
        config: TransportConfig | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> ApiClient:
        return cls(build_client(origin, config, transport=transport), origin=origin)

    @property
    def origin(self) -> str:
        return self._origin

    def has_session_cookies(self) -> bool:
        """Return True when the in-memory cookie jar is non-empty."""
        return len(self._client.cookies.jar) > 0

    def clear_session_cookies(self) -> None:
        """Drop all session cookies (used on logout)."""
        self._client.cookies.clear()

    def close(self) -> None:
        self._client.close()

    # -- auth -----------------------------------------------------------------

    def login(self, secret: str) -> AppLoginResponse:
        """POST the application secret; the session cookie is stored by the jar."""
        response = self._request(
            "POST", "auth/app-login", json_body={"client_secret": secret}, expect=_OK
        )
        return self._decode(response, AppLoginResponse.model_validate, "POST", "auth/app-login")

    def check_auth(self) -> AuthCheckResponse:
        response = self._request("GET", "auth/check", expect=_OK)
        return self._decode(response, AuthCheckResponse.model_validate, "GET", "auth/check")

    # -- health / dashboard ---------------------------------------------------

    def live(self) -> LiveResponse:
        """Public liveness probe (absolute URL, outside ``/api/v1``)."""
        url = live_url(self._origin)
        response = self._request("GET", url, expect=_OK)
        return self._decode(response, LiveResponse.model_validate, "GET", url)

    def ready(self) -> ReadyResponse:
        response = self._request("GET", "health/ready", expect=_OK)
        return self._decode(response, ReadyResponse.model_validate, "GET", "health/ready")

    def health_status(self) -> HealthStatusResponse:
        response = self._request("GET", "health/status", expect=_OK)
        return self._decode(response, HealthStatusResponse.model_validate, "GET", "health/status")

    def dashboard_summary(self) -> DashboardSummaryResponse:
        response = self._request("GET", "dashboard/summary", expect=_OK)
        return self._decode(
            response, DashboardSummaryResponse.model_validate, "GET", "dashboard/summary"
        )

    # -- groups ---------------------------------------------------------------

    def list_groups(self) -> list[GroupResponse]:
        response = self._request("GET", "groups", expect=_OK)
        return self._decode(response, _GROUP_LIST.validate_python, "GET", "groups")

    def get_group(self, group_id: int) -> GroupResponse:
        path = f"groups/{group_id}"
        response = self._request("GET", path, expect=_OK)
        return self._decode(response, GroupResponse.model_validate, "GET", path)

    def create_group(self, payload: GroupCreateRequest) -> GroupResponse:
        response = self._request(
            "POST", "groups", json_body=payload.model_dump(exclude_none=True), expect=_CREATED
        )
        return self._decode(response, GroupResponse.model_validate, "POST", "groups")

    def patch_group(self, group_id: int, payload: GroupPatchRequest) -> GroupResponse:
        path = f"groups/{group_id}"
        response = self._request(
            "PATCH", path, json_body=payload.model_dump(exclude_none=True), expect=_OK
        )
        return self._decode(response, GroupResponse.model_validate, "PATCH", path)

    def delete_group(self, group_id: int) -> None:
        """Delete a group. ``409`` (in use) maps to :attr:`ErrorKind.CONFLICT`."""
        path = f"groups/{group_id}"
        self._request("DELETE", path, expect=_NO_CONTENT)

    # -- filters --------------------------------------------------------------

    def list_filters(self) -> list[FilterResponse]:
        response = self._request("GET", "filters", expect=_OK)
        return self._decode(response, _FILTER_LIST.validate_python, "GET", "filters")

    def create_filter(self, payload: FilterCreateRequest) -> FilterResponse:
        response = self._request("POST", "filters", json_body=payload.model_dump(), expect=_CREATED)
        return self._decode(response, FilterResponse.model_validate, "POST", "filters")

    def delete_filter(self, filter_id: int) -> None:
        path = f"filters/{filter_id}"
        self._request("DELETE", path, expect=_NO_CONTENT)

    # -- settings -------------------------------------------------------------

    def get_settings(self) -> SettingsResponse:
        response = self._request("GET", "settings", expect=_OK)
        return self._decode(response, SettingsResponse.model_validate, "GET", "settings")

    def patch_settings(self, payload: SettingsPatchRequest) -> SettingsResponse:
        response = self._request(
            "PATCH", "settings", json_body=payload.model_dump(exclude_none=True), expect=_OK
        )
        return self._decode(response, SettingsResponse.model_validate, "PATCH", "settings")

    # -- internals ------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, object] | None = None,
        expect: tuple[int, ...] = _OK,
    ) -> httpx.Response:
        try:
            response = self._client.request(method, path, json=json_body)
        except httpx.TimeoutException as exc:
            raise ApiError(ErrorKind.TIMEOUT, method=method, path=path) from exc
        except httpx.TransportError as exc:
            raise ApiError(ErrorKind.NETWORK, method=method, path=path) from exc
        except httpx.HTTPError as exc:
            raise ApiError(ErrorKind.NETWORK, method=method, path=path) from exc

        if response.status_code not in expect:
            raise error_from_http(
                response.status_code,
                self._safe_json(response),
                method=method,
                path=path,
            )
        return response

    @staticmethod
    def _safe_json(response: httpx.Response) -> object | None:
        try:
            payload: object = response.json()
        except ValueError:
            return None
        return payload

    @staticmethod
    def _decode(
        response: httpx.Response,
        load: Callable[[object], _T],
        method: str,
        path: str,
    ) -> _T:
        try:
            payload: object = response.json()
        except ValueError as exc:
            raise ApiError(ErrorKind.DECODE, method=method, path=path) from exc
        try:
            return load(payload)
        except (ValidationError, TypeError, ValueError) as exc:
            raise ApiError(ErrorKind.DECODE, method=method, path=path) from exc
