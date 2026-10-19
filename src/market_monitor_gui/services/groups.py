"""Groups use-case: list (with cache fallback) and CRUD through the session.

Reads fall back to the last-known cached list only when the network is unavailable;
writes are one-shot and are never replayed. Destructive ``409`` surfaces as
:attr:`ErrorKind.CONFLICT` for the caller to handle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import TypeAdapter, ValidationError

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.dto import GroupCreateRequest, GroupPatchRequest, GroupResponse
from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.auth.session import SessionManager
from market_monitor_gui.db.cache import CacheKey, CacheStore, JsonValue

_GROUP_LIST: TypeAdapter[list[GroupResponse]] = TypeAdapter(list[GroupResponse])

_CACHE_FALLBACK_KINDS = (ErrorKind.NETWORK, ErrorKind.TIMEOUT)


@dataclass(frozen=True, slots=True)
class GroupsData:
    """A list of groups, with cache provenance for the offline label."""

    groups: tuple[GroupResponse, ...]
    from_cache: bool
    cached_at: datetime | None


def load_groups(session: SessionManager, api: ApiClient, cache: CacheStore) -> GroupsData:
    """List groups, falling back to the cached list when the network is unavailable."""
    try:
        groups = session.read(api.list_groups)
    except ApiError as exc:
        if exc.kind not in _CACHE_FALLBACK_KINDS:
            raise
        entry = cache.load(api.origin, CacheKey.GROUPS.value)
        if entry is None:
            raise
        cached = _parse_groups(entry.payload)
        if cached is None:
            raise
        return GroupsData(tuple(cached), from_cache=True, cached_at=entry.fetched_at)

    payload: JsonValue = [group.model_dump(mode="json") for group in groups]
    cache.set_json(api.origin, CacheKey.GROUPS.value, payload)
    return GroupsData(tuple(groups), from_cache=False, cached_at=None)


def create_group(
    session: SessionManager,
    api: ApiClient,
    *,
    name: str,
    url: str,
    enabled: bool,
) -> GroupResponse:
    """Create a group. The server validates; the UI never guesses the result."""
    payload = GroupCreateRequest(name=name, url=url, enabled=enabled)
    return session.write(lambda: api.create_group(payload))


def update_group(
    session: SessionManager,
    api: ApiClient,
    group_id: int,
    *,
    name: str,
    url: str,
    enabled: bool,
) -> GroupResponse:
    """Patch a group's editable fields."""
    payload = GroupPatchRequest(name=name, url=url, enabled=enabled)
    return session.write(lambda: api.patch_group(group_id, payload))


def set_group_enabled(
    session: SessionManager,
    api: ApiClient,
    group_id: int,
    *,
    enabled: bool,
) -> GroupResponse:
    """Enable or disable a single group (sends only the ``enabled`` field)."""
    payload = GroupPatchRequest(enabled=enabled)
    return session.write(lambda: api.patch_group(group_id, payload))


def delete_group(session: SessionManager, api: ApiClient, group_id: int) -> None:
    """Delete a group; ``409`` propagates as :attr:`ErrorKind.CONFLICT`."""
    session.write(lambda: api.delete_group(group_id))


def _parse_groups(payload: JsonValue) -> list[GroupResponse] | None:
    try:
        return _GROUP_LIST.validate_python(payload)
    except ValidationError:
        return None
