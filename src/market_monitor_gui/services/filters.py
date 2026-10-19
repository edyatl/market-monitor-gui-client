"""Filters (exclusions) use-case: list (with cache fallback), add and delete.

Reads fall back to the last-known cached list only when the network is unavailable;
writes are one-shot and are never replayed. A filter is created from its ``phrase``
alone: the API create model has no ``enabled`` field, so none is ever sent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import TypeAdapter, ValidationError

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.dto import FilterCreateRequest, FilterResponse
from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.auth.session import SessionManager
from market_monitor_gui.db.cache import CacheKey, CacheStore, JsonValue

_FILTER_LIST: TypeAdapter[list[FilterResponse]] = TypeAdapter(list[FilterResponse])

_CACHE_FALLBACK_KINDS = (ErrorKind.NETWORK, ErrorKind.TIMEOUT)


@dataclass(frozen=True, slots=True)
class FiltersData:
    """A list of exclusion filters, with cache provenance for the offline label."""

    filters: tuple[FilterResponse, ...]
    from_cache: bool
    cached_at: datetime | None


def load_filters(session: SessionManager, api: ApiClient, cache: CacheStore) -> FiltersData:
    """List filters, falling back to the cached list when the network is unavailable."""
    try:
        filters = session.read(api.list_filters)
    except ApiError as exc:
        if exc.kind not in _CACHE_FALLBACK_KINDS:
            raise
        entry = cache.load(api.origin, CacheKey.FILTERS.value)
        if entry is None:
            raise
        cached = _parse_filters(entry.payload)
        if cached is None:
            raise
        return FiltersData(tuple(cached), from_cache=True, cached_at=entry.fetched_at)

    payload: JsonValue = [item.model_dump(mode="json") for item in filters]
    cache.set_json(api.origin, CacheKey.FILTERS.value, payload)
    return FiltersData(tuple(filters), from_cache=False, cached_at=None)


def create_filter(session: SessionManager, api: ApiClient, *, phrase: str) -> FilterResponse:
    """Add an exclusion phrase. The server validates; the UI never guesses the result."""
    payload = FilterCreateRequest(phrase=phrase)
    return session.write(lambda: api.create_filter(payload))


def delete_filter(session: SessionManager, api: ApiClient, filter_id: int) -> None:
    """Delete an exclusion filter."""
    session.write(lambda: api.delete_filter(filter_id))


def _parse_filters(payload: JsonValue) -> list[FilterResponse] | None:
    try:
        return _FILTER_LIST.validate_python(payload)
    except ValidationError:
        return None
