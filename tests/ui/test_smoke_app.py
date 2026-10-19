"""Optional smoke test: constructing the shell requires a display.

Skipped unless ``DISPLAY``/``WAYLAND_DISPLAY`` is set (e.g. under ``xvfb-run``).
"""

from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from typing import Any, cast

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


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_sidebar_meets_content_without_gap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: no accidental stripe between the sidebar and the content area."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        sidebar, content = shell._sidebar, shell._content
        assert sidebar.winfo_width() == shell.grid_bbox(0, 0)[2]
        assert content.winfo_x() == sidebar.winfo_x() + sidebar.winfo_width()
        shell.destroy()
    finally:
        context.close()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_sidebar_order_is_overview_groups_filters_settings_help(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell
    from market_monitor_gui.ui.navigation import SCREEN_ORDER, Screen

    context = AppContext.create()
    try:
        shell = Shell(context)
        assert list(SCREEN_ORDER) == [
            Screen.OVERVIEW,
            Screen.GROUPS,
            Screen.FILTERS,
            Screen.SETTINGS,
            Screen.HELP,
        ]
        assert shell._sidebar._buttons  # built in the declared order
        shell.destroy()
    finally:
        context.close()


class _Click:
    """Minimal stand-in for a Tk click event for the menu dismiss handler."""

    def __init__(self, widget: object) -> None:
        self.widget: Any = widget


def _click_event(widget: object) -> tk.Event[tk.Misc]:
    return cast("tk.Event[tk.Misc]", _Click(widget))


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_menu_opens_on_click_and_dismisses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The menu is click-toggle: one click opens it and it stays open until dismissed."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        menu = shell._menu
        assert not menu._is_open()
        menu.toggle()
        shell.update()
        assert menu._is_open()
        assert menu._popup is not None
        assert len(menu._popup.winfo_children()) == 4
        menu.toggle()
        shell.update()
        assert not menu._is_open()

        # Clicking away dismisses.
        menu.open()
        shell.update()
        menu._on_any_click(_click_event(shell))
        shell.update()
        assert not menu._is_open()

        # Clicking the menu button while open closes and does not reopen.
        menu.open()
        shell.update()
        menu._press_while_open = True
        menu._on_any_click(_click_event(shell))
        shell.update()
        assert not menu._is_open()
        menu.toggle()
        shell.update()
        assert not menu._is_open()
        shell.destroy()
    finally:
        context.close()
