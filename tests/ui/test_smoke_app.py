"""Optional smoke test: constructing the shell requires a display.

Skipped unless ``DISPLAY``/``WAYLAND_DISPLAY`` is set (e.g. under ``xvfb-run``).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_shell_constructs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update_idletasks()
        assert shell.winfo_exists()
        shell.destroy()
    finally:
        context.close()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_menu_button_not_clipped_by_status_bar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: the sidebar footer Menu button must sit fully above the status bar."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        menu = shell._menu.button
        status_bar = shell._status_bar
        assert menu.winfo_height() >= 20
        assert menu.winfo_rooty() + menu.winfo_height() <= status_bar.winfo_rooty()
        shell.destroy()
    finally:
        context.close()
