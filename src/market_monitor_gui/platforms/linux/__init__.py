"""Linux per-user data directory resolution."""

from __future__ import annotations

import os
from pathlib import Path

from market_monitor_gui.platforms._constants import APP_DIR_NAME


def data_dir() -> Path:
    """Return the Linux per-user data directory for the application.

    Follows the XDG base directory spec: ``$XDG_DATA_HOME`` when set, otherwise
    ``~/.local/share``. The directory is not created here.
    """
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    root = Path(xdg_data_home).expanduser() if xdg_data_home else Path.home() / ".local" / "share"
    return root / APP_DIR_NAME
