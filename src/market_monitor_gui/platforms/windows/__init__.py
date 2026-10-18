"""Windows per-user data directory resolution."""

from __future__ import annotations

import os
from pathlib import Path

from market_monitor_gui.platforms._constants import APP_DIR_NAME


def data_dir() -> Path:
    """Return the Windows per-user data directory for the application.

    Uses ``%LOCALAPPDATA%``, falling back to ``~/AppData/Local``. The directory is
    not created here. No DPAPI or keyring is used; secret material at rest is
    handled by the Fernet secret store.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    root = (
        Path(local_app_data).expanduser() if local_app_data else Path.home() / "AppData" / "Local"
    )
    return root / APP_DIR_NAME
