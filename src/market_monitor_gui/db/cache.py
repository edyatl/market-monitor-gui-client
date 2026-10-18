"""Last-known API payloads stored in SQLite for offline display.

The cache is **not** a source of truth. It only lets screens show the most recent
successful response (clearly labelled as cached) while offline. Entries are scoped
by server origin so switching servers never mixes data. Payloads are stored as JSON
so this layer needs no knowledge of the API DTOs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from market_monitor_gui.db._time import parse_iso, utc_now, utc_now_iso
from market_monitor_gui.db.database import Database

type JsonValue = dict[str, JsonValue] | list[JsonValue] | str | int | float | bool | None

TABLE = "cache_entries"


class CacheKey(StrEnum):
    """Canonical cache entry names used by the services layer."""

    GROUPS = "groups"
    FILTERS = "filters"
    SETTINGS = "settings"
    HEALTH_STATUS = "health_status"
    DASHBOARD_SUMMARY = "dashboard_summary"


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """A cached payload together with when it was fetched."""

    server: str
    key: str
    payload: JsonValue
    fetched_at: datetime

    @property
    def age_seconds(self) -> float:
        """Seconds since the payload was fetched (never negative)."""
        return max(0.0, (utc_now() - self.fetched_at).total_seconds())


class CacheStore:
    """Read/write helpers for the ``cache_entries`` table."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def set_json(self, server: str, key: str, payload: JsonValue) -> None:
        """Store ``payload`` as JSON for ``server``/``key``, replacing any previous value."""
        self._db.execute(
            f"""
            INSERT INTO {TABLE} (server, key, payload, fetched_at) VALUES (?, ?, ?, ?)
            ON CONFLICT(server, key) DO UPDATE SET payload = excluded.payload,
                                                   fetched_at = excluded.fetched_at
            """,
            (server, key, json.dumps(payload, ensure_ascii=False), utc_now_iso()),
        )

    def load(self, server: str, key: str) -> CacheEntry | None:
        """Return the cached entry, or ``None`` when missing or unreadable."""
        row = self._db.query_one(
            f"SELECT payload, fetched_at FROM {TABLE} WHERE server = ? AND key = ?",
            (server, key),
        )
        if row is None:
            return None
        try:
            payload: JsonValue = json.loads(row["payload"])
            fetched_at = parse_iso(str(row["fetched_at"]))
        except ValueError, TypeError:
            return None
        return CacheEntry(server=server, key=key, payload=payload, fetched_at=fetched_at)

    def delete(self, server: str, key: str) -> None:
        self._db.execute(f"DELETE FROM {TABLE} WHERE server = ? AND key = ?", (server, key))

    def clear(self, server: str) -> None:
        """Drop every entry for one server origin."""
        self._db.execute(f"DELETE FROM {TABLE} WHERE server = ?", (server,))

    def clear_all(self) -> None:
        self._db.execute(f"DELETE FROM {TABLE}")
