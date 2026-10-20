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


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_cached_data_locks_settings_and_shows_role_colours(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G14: cached settings are read-only and primary actions stay accent-filled."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from datetime import UTC, datetime

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.services.settings import SettingsData
    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        settings = shell._settings_screen
        settings.render(
            SettingsData(
                price_drop_threshold_percent=10.0,
                from_cache=True,
                cached_at=datetime.now(UTC),
            )
        )
        shell.update()

        assert settings._entry.cget("state") == "disabled"
        assert settings._save_button.cget("state") == "disabled"
        assert settings._save_button.cget("fg_color") == theme.colour("disabled_surface")
        assert shell._groups_screen._add_button.cget("fg_color") == theme.colour("accent")
        assert shell._filters_screen._add_button.cget("text_color") == theme.colour("on_accent")
        shell.destroy()
    finally:
        context.close()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_sidebar_and_menu_show_decorative_icons(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G13: navigation labels carry their icon glyph, and the menu button too."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui.app import Shell
    from market_monitor_gui.ui.navigation import SCREEN_ICONS, screen_button_text

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        for screen, button in shell._sidebar._buttons.items():
            text = str(button.cget("text"))
            assert SCREEN_ICONS[screen] in text
            assert text == screen_button_text(screen)
        assert ru.MENU_ICON in str(shell._menu.button.cget("text"))
        shell.destroy()
    finally:
        context.close()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_scrollable_screens_opt_into_wheel_scrolling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G13: every scrollable screen area enables X11 wheel scrolling."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        frames = (
            shell._groups_screen._list,
            shell._filters_screen._list,
            shell._help_screen._scroll,
        )
        for frame in frames:
            assert frame._mm_wheel_bound is True
        shell.destroy()
    finally:
        context.close()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_screens_share_the_single_banner_widget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G15: Overview/Groups/Filters/Settings all use the shared Banner widget."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell
    from market_monitor_gui.ui.banner import Banner
    from market_monitor_gui.ui.navigation import Screen

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        screens = (
            shell._screens[Screen.OVERVIEW],
            shell._groups_screen,
            shell._filters_screen,
            shell._settings_screen,
        )
        for screen in screens:
            assert isinstance(screen._banner, Banner)
        shell.destroy()
    finally:
        context.close()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_banner_sits_above_the_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """G15: the lazily packed banner still appears above the screen's content."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell
    from market_monitor_gui.ui.navigation import Screen

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        pairs = (
            (shell._screens[Screen.OVERVIEW], shell._screens[Screen.OVERVIEW]._cards, "before"),
            (shell._groups_screen, shell._groups_screen._toolbar, "after"),
            (shell._filters_screen, shell._filters_screen._toolbar, "after"),
            (shell._settings_screen, shell._settings_screen._field_row, "before"),
        )
        for screen, anchor, relation in pairs:
            screen.set_loading()
            shell.update()
            assert screen._banner.winfo_manager() == "pack"
            # ``pack_info`` does not report before/after; compare pack order instead.
            siblings = screen.body.pack_slaves()
            banner_index = siblings.index(screen._banner)
            anchor_index = siblings.index(anchor)
            if relation == "before":
                assert banner_index < anchor_index
            else:
                assert anchor_index < banner_index == anchor_index + 1
        shell.destroy()
    finally:
        context.close()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_list_counts_live_on_the_toolbar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """G16: the count sits on the toolbar row (actions left, count right)."""
    monkeypatch.setenv("MARKET_MONITOR_GUI_DATA_DIR", str(tmp_path))

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
        shell.update()
        for screen in (shell._groups_screen, shell._filters_screen):
            assert screen._count.master is screen._toolbar
            toolbar_slaves = screen._toolbar.pack_slaves()
            assert screen._count in toolbar_slaves
            assert toolbar_slaves.index(screen._count) > toolbar_slaves.index(screen._add_button)
            assert screen._count not in screen.body.pack_slaves()
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
