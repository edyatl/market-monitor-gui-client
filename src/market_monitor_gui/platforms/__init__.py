"""OS-specific concerns: data directory resolution and frozen-build detection.

The application stores its configuration, encrypted secret, and SQLite database in
a **per-user** data directory only. It never writes beside the executable and never
into a Nuitka one-file extraction directory (``sys._MEIPASS`` / temp extract path),
which is ephemeral and may be read-only.

Override for tests and diagnostics: ``MARKET_MONITOR_GUI_DATA_DIR``.
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

from market_monitor_gui.platforms import linux, windows
from market_monitor_gui.platforms._constants import APP_DIR_NAME, DATA_DIR_ENV

__all__ = [
    "APP_DIR_NAME",
    "DATA_DIR_ENV",
    "data_dir",
    "ensure_data_dir",
    "executable_dir",
    "is_frozen",
]

_DIR_MODE = 0o700


def is_frozen() -> bool:
    """Return True when running from a packaged build (PyInstaller or Nuitka)."""
    return bool(getattr(sys, "frozen", False)) or "__compiled__" in globals()


def executable_dir() -> Path:
    """Return the directory of the real executable (never the extract temp dir).

    Exposed for packaging diagnostics; configuration and data do **not** live here.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(sys.argv[0]).resolve().parent


def data_dir() -> Path:
    """Return the per-user data directory (does not create it).

    Resolution order: ``MARKET_MONITOR_GUI_DATA_DIR`` override, then the
    platform-specific per-user location.
    """
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        return windows.data_dir()
    return linux.data_dir()


def ensure_data_dir() -> Path:
    """Create the data directory if needed and return it.

    On POSIX the directory is created with owner-only permissions (``0o700``).
    """
    path = data_dir()
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        # Best effort: a pre-existing directory with looser bits must not crash startup.
        with contextlib.suppress(OSError):
            path.chmod(_DIR_MODE)
    return path
