"""Settings use-case: read the global price-drop threshold and patch it.

Reads fall back to the last-known cached value only when the network is unavailable;
the write is one-shot and is never replayed. The PATCH body carries only
``price_drop_threshold_percent`` (the API model forbids additional fields), and the
cache is refreshed with the server-confirmed response so an offline view stays honest.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import ValidationError

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.dto import SettingsPatchRequest, SettingsResponse
from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.auth.session import SessionManager
from market_monitor_gui.db.cache import CacheKey, CacheStore, JsonValue
from market_monitor_gui.texts import ru

_CACHE_FALLBACK_KINDS = (ErrorKind.NETWORK, ErrorKind.TIMEOUT)


@dataclass(frozen=True, slots=True)
class SettingsData:
    """The global settings, with cache provenance for the offline label."""

    price_drop_threshold_percent: float
    from_cache: bool
    cached_at: datetime | None


def load_settings(session: SessionManager, api: ApiClient, cache: CacheStore) -> SettingsData:
    """Read settings, falling back to the cached value when the network is unavailable."""
    try:
        settings = session.read(api.get_settings)
    except ApiError as exc:
        if exc.kind not in _CACHE_FALLBACK_KINDS:
            raise
        entry = cache.load(api.origin, CacheKey.SETTINGS.value)
        if entry is None:
            raise
        cached = _parse_settings(entry.payload)
        if cached is None:
            raise
        return SettingsData(
            cached.price_drop_threshold_percent,
            from_cache=True,
            cached_at=entry.fetched_at,
        )

    cache.set_json(api.origin, CacheKey.SETTINGS.value, settings.model_dump(mode="json"))
    return SettingsData(
        settings.price_drop_threshold_percent,
        from_cache=False,
        cached_at=None,
    )


def save_settings(
    session: SessionManager,
    api: ApiClient,
    cache: CacheStore,
    *,
    price_drop_threshold_percent: float,
) -> SettingsResponse:
    """Patch the global threshold and return the server-confirmed settings.

    An out-of-range value is rejected locally before any request is made, and the
    cache is updated from the response so the offline view matches the server.
    """
    try:
        payload = SettingsPatchRequest(price_drop_threshold_percent=price_drop_threshold_percent)
    except ValidationError as exc:
        raise ApiError(ErrorKind.VALIDATION, text_key=ru.ERR_VALIDATION) from exc
    saved = session.write(lambda: api.patch_settings(payload))
    cache.set_json(api.origin, CacheKey.SETTINGS.value, saved.model_dump(mode="json"))
    return saved


def _parse_settings(payload: JsonValue) -> SettingsResponse | None:
    try:
        return SettingsResponse.model_validate(payload)
    except ValidationError:
        return None
