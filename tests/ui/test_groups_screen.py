"""G13/G14: group rows use role-styled controls and lock mutations when offline."""

from __future__ import annotations

import os
import tkinter as tk
from datetime import UTC, datetime
from typing import Any

import pytest

pytestmark = pytest.mark.e2e


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _walk(widget: tk.Misc) -> list[tk.Misc]:
    found: list[tk.Misc] = []
    for child in widget.winfo_children():
        found.append(child)
        found.extend(_walk(child))
    return found


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_group_url_button_reports_the_url() -> None:
    import customtkinter as ctk

    from market_monitor_gui.api.dto import GroupResponse
    from market_monitor_gui.services.groups import GroupsData
    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.screens.groups import GroupsScreen

    root = ctk.CTk()
    try:
        fonts = theme.build_fonts()
        opened: list[str] = []
        screen = GroupsScreen(
            root,
            fonts=fonts,
            on_refresh=lambda: None,
            on_add=lambda: None,
            on_edit=lambda _group: None,
            on_toggle=lambda _group: None,
            on_delete=lambda _group: None,
            on_open_url=opened.append,
        )
        screen.pack(fill="both", expand=True)
        group = GroupResponse(
            id=1,
            name="G1",
            url="https://shop.example/1",
            enabled=True,
            sort_order=0,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        screen.render(GroupsData((group,), from_cache=False, cached_at=None))
        root.update()

        url_buttons = [
            child
            for child in _walk(screen)
            if isinstance(child, ctk.CTkButton) and child.cget("text") == group.url
        ]
        assert len(url_buttons) == 1
        assert isinstance(screen._list, ctk.CTkScrollableFrame)

        url_buttons[0].invoke()
        assert opened == [group.url]
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_group_url_button_is_link_styled() -> None:
    import customtkinter as ctk

    from market_monitor_gui.api.dto import GroupResponse
    from market_monitor_gui.services.groups import GroupsData
    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.screens.groups import GroupsScreen

    root = ctk.CTk()
    try:
        fonts = theme.build_fonts()
        screen = GroupsScreen(
            root,
            fonts=fonts,
            on_refresh=lambda: None,
            on_add=lambda: None,
            on_edit=lambda _group: None,
            on_toggle=lambda _group: None,
            on_delete=lambda _group: None,
            on_open_url=lambda _url: None,
        )
        screen.pack(fill="both", expand=True)
        group = GroupResponse(
            id=1,
            name="G1",
            url="https://shop.example/1",
            enabled=True,
            sort_order=0,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        screen.render(GroupsData((group,), from_cache=False, cached_at=None))
        root.update()

        url_button = next(
            child
            for child in _walk(screen)
            if isinstance(child, ctk.CTkButton) and child.cget("text") == group.url
        )
        assert url_button.cget("fg_color") == "transparent"
        assert url_button.cget("text_color") == theme.colour("accent")
        assert bool(fonts.link.cget("underline")) is True
    finally:
        root.destroy()


def _group() -> Any:
    from market_monitor_gui.api.dto import GroupResponse

    return GroupResponse(
        id=1,
        name="G1",
        url="https://shop.example/1",
        enabled=True,
        sort_order=0,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def _screen(root: Any) -> Any:
    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.screens.groups import GroupsScreen

    screen = GroupsScreen(
        root,
        fonts=theme.build_fonts(),
        on_refresh=lambda: None,
        on_add=lambda: None,
        on_edit=lambda _group: None,
        on_toggle=lambda _group: None,
        on_delete=lambda _group: None,
        on_open_url=lambda _url: None,
    )
    screen.pack(fill="both", expand=True)
    return screen


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_cached_data_locks_mutations_but_not_the_url_link() -> None:
    import customtkinter as ctk

    from market_monitor_gui.services.groups import GroupsData
    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui import theme

    root = ctk.CTk()
    try:
        screen = _screen(root)
        screen.render(GroupsData((_group(),), from_cache=True, cached_at=datetime.now(UTC)))
        root.update()

        assert screen._add_button.cget("state") == "disabled"
        assert screen._add_button.cget("fg_color") == theme.colour("disabled_surface")
        row = screen._rows[1]
        assert row._edit.cget("state") == "disabled"
        assert row._toggle.cget("state") == "disabled"
        assert row._delete.cget("state") == "disabled"
        # Opening a link is not a mutation.
        assert row._open_url.cget("state") == "normal"
        assert ru.DATA_CACHED_READONLY.split("{when}")[0] in screen._banner.text
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_row_actions_use_role_colours() -> None:
    import customtkinter as ctk

    from market_monitor_gui.services.groups import GroupsData
    from market_monitor_gui.ui import theme

    root = ctk.CTk()
    try:
        screen = _screen(root)
        screen.render(GroupsData((_group(),), from_cache=False, cached_at=None))
        root.update()

        row = screen._rows[1]
        assert screen._add_button.cget("fg_color") == theme.colour("accent")
        assert screen._refresh_button.cget("fg_color") == "transparent"
        assert row._toggle.cget("fg_color") == "transparent"
        assert row._delete.cget("fg_color") == theme.colour("error")
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_failed_read_locks_and_failed_write_keeps_controls_usable() -> None:
    import customtkinter as ctk

    from market_monitor_gui.api.errors import ApiError, ErrorKind
    from market_monitor_gui.services.errors import text_key_for_exception
    from market_monitor_gui.services.groups import GroupsData
    from market_monitor_gui.texts import ru

    root = ctk.CTk()
    try:
        screen = _screen(root)
        screen.render(GroupsData((_group(),), from_cache=False, cached_at=None))
        root.update()

        screen.show_write_error(text_key_for_exception(ApiError(ErrorKind.CONFLICT)))
        root.update()
        assert screen._add_button.cget("state") == "normal"
        assert screen._rows[1]._delete.cget("state") == "normal"
        assert screen._banner.text == ru.ERR_CONFLICT

        screen.show_read_error(text_key_for_exception(ApiError(ErrorKind.TIMEOUT)))
        root.update()
        assert screen._add_button.cget("state") == "disabled"
        assert screen._rows[1]._toggle.cget("state") == "disabled"
        assert ru.READONLY_NOTICE in screen._banner.text
    finally:
        root.destroy()
