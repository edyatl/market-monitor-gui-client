"""Optional smoke test: constructing the shell requires a display.

Skipped unless ``DISPLAY``/``WAYLAND_DISPLAY`` is set (e.g. under ``xvfb-run``).
"""

from __future__ import annotations

import os
import tkinter as tk
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


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_menu_anchored_and_stays_open(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One click posts a menu next to the button; it stays open until dismissed."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        menu = shell._menu
        button = menu.button
        assert not menu._is_open()

        menu.toggle()
        shell.update()
        assert menu._is_open()
        assert menu._menu.winfo_ismapped()

        # Anchored to the button (never the top-left of the screen) and above it.
        assert menu._menu.winfo_rootx() == button.winfo_rootx()
        assert menu._menu.winfo_rootx() > 5
        assert menu._menu.winfo_rooty() < button.winfo_rooty()

        # Exactly the four operator actions.
        last = menu._menu.index("end")
        assert last is not None
        commands = [i for i in range(last + 1) if menu._menu.type(i) == "command"]
        assert len(commands) == 4

        # Stays open across event processing (no press-and-hold, no self-dismiss).
        shell.update_idletasks()
        shell.update()
        assert menu._is_open()

        # A second click of the button closes it.
        menu.toggle()
        shell.update()
        assert not menu._is_open()

        # Explicit close (item selection / Escape / click-outside use the same path).
        menu.open()
        shell.update()
        assert menu._is_open()
        menu.close()
        shell.update()
        assert not menu._is_open()
        shell.destroy()
    finally:
        context.close()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_settings_and_filters_are_real_screens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G10/G11: Settings and Filters replace their placeholders."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell
    from market_monitor_gui.ui.navigation import Screen
    from market_monitor_gui.ui.screens.filters import FiltersScreen
    from market_monitor_gui.ui.screens.settings import SettingsScreen

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        assert isinstance(shell._screens[Screen.SETTINGS], SettingsScreen)
        assert isinstance(shell._screens[Screen.FILTERS], FiltersScreen)
        # The screens build their controls without a display-only failure.
        assert shell._settings_screen._entry.winfo_exists()
        assert shell._filters_screen._add_button.winfo_exists()
        shell.destroy()
    finally:
        context.close()


def _walk(widget: tk.Misc) -> list[tk.Misc]:
    """Return every descendant widget, depth-first."""
    found: list[tk.Misc] = []
    for child in widget.winfo_children():
        found.append(child)
        found.extend(_walk(child))
    return found


def _label_texts(widget: tk.Misc) -> list[str]:
    """Collect the text of every CTkLabel in the widget tree (depth-first)."""
    import customtkinter as ctk

    return [str(child.cget("text")) for child in _walk(widget) if isinstance(child, ctk.CTkLabel)]


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_help_is_a_real_static_screen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """G12: Help is a real read-only screen whose static guide is rendered."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    import customtkinter as ctk

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui.app import Shell
    from market_monitor_gui.ui.navigation import Screen
    from market_monitor_gui.ui.screens.help import HelpScreen

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        help_screen = shell._screens[Screen.HELP]
        assert isinstance(help_screen, HelpScreen)
        assert isinstance(help_screen._scroll, ctk.CTkScrollableFrame)

        texts = _label_texts(help_screen)
        assert ru.HELP_INTRO_HEADING in texts
        assert ru.HELP_INTRO_BODY in texts
        assert ru.HELP_SUPPORT_HEADING in texts
        assert ru.HELP_SUPPORT_BODY in texts

        # Read-only: no inputs, no buttons anywhere in the screen.
        for child in _walk(help_screen):
            assert not isinstance(child, (ctk.CTkEntry, ctk.CTkButton))
        shell.destroy()
    finally:
        context.close()
