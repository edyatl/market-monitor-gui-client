"""Shared path constants (kept dependency-free to avoid import cycles)."""

from __future__ import annotations

from typing import Final

#: Directory name used under the platform's per-user data root.
APP_DIR_NAME: Final[str] = "market-monitor-gui"

#: Environment variable that overrides the data directory (also used by tests).
DATA_DIR_ENV: Final[str] = "MARKET_MONITOR_GUI_DATA_DIR"
