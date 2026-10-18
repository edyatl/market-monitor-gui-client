"""Key/value UI state stored in SQLite.

This is *not* a source of truth for anything the server owns: only local UI
preferences (theme, last screen, window geometry) and small client settings live
here. The API base URL is owned by the config store, not by this table.
"""

from __future__ import annotations

from market_monitor_gui.db._time import utc_now_iso
from market_monitor_gui.db.database import Database

KEY_THEME = "theme"
KEY_LAST_SCREEN = "last_screen"
KEY_WINDOW_GEOMETRY = "window_geometry"

DEFAULT_THEME = "system"


class UiStateStore:
    """Read/write helpers for the ``ui_state`` table."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self._db.query_one("SELECT value FROM ui_state WHERE key = ?", (key,))
        if row is None:
            return default
        return str(row["value"])

    def set(self, key: str, value: str) -> None:
        self._db.execute(
            """
            INSERT INTO ui_state (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                                           updated_at = excluded.updated_at
            """,
            (key, value, utc_now_iso()),
        )

    def delete(self, key: str) -> None:
        self._db.execute("DELETE FROM ui_state WHERE key = ?", (key,))

    def all_items(self) -> dict[str, str]:
        rows = self._db.query_all("SELECT key, value FROM ui_state")
        return {str(row["key"]): str(row["value"]) for row in rows}

    # -- typed convenience accessors -----------------------------------------

    def get_theme(self) -> str:
        return self.get(KEY_THEME, DEFAULT_THEME) or DEFAULT_THEME

    def set_theme(self, theme: str) -> None:
        self.set(KEY_THEME, theme)

    def get_last_screen(self) -> str | None:
        return self.get(KEY_LAST_SCREEN)

    def set_last_screen(self, screen: str) -> None:
        self.set(KEY_LAST_SCREEN, screen)

    def get_window_geometry(self) -> str | None:
        return self.get(KEY_WINDOW_GEOMETRY)

    def set_window_geometry(self, geometry: str) -> None:
        self.set(KEY_WINDOW_GEOMETRY, geometry)
