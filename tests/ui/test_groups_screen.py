"""G13: the group URL is a link-styled button that reports the group's URL (needs a display)."""

from __future__ import annotations

import os
import tkinter as tk

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
