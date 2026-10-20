"""G14: the Filters screen locks mutations for cached or unavailable data (needs a display)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import pytest

pytestmark = pytest.mark.e2e


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _make_screen() -> tuple[Any, Any, Any]:
    import customtkinter as ctk

    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.screens.filters import FiltersScreen

    root = ctk.CTk()
    screen = FiltersScreen(
        root,
        fonts=theme.build_fonts(),
        on_refresh=lambda: None,
        on_add=lambda: None,
        on_delete=lambda _item: None,
    )
    screen.pack(fill="both", expand=True)
    return root, screen, theme


def _item() -> Any:
    from market_monitor_gui.api.dto import FilterResponse

    return FilterResponse(
        id=1,
        phrase="чехол",
        normalized_phrase="чехол",
        enabled=True,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_cached_data_locks_every_mutation() -> None:
    from market_monitor_gui.services.filters import FiltersData
    from market_monitor_gui.texts import ru

    root, screen, theme = _make_screen()
    try:
        screen.render(FiltersData((_item(),), from_cache=True, cached_at=datetime.now(UTC)))
        root.update()

        assert screen._add_button.cget("state") == "disabled"
        assert screen._add_button.cget("fg_color") == theme.colour("disabled_surface")
        row = screen._rows[1]
        assert row._delete.cget("state") == "disabled"
        assert row._delete.cget("fg_color") == theme.colour("disabled_surface")
        assert ru.DATA_CACHED_READONLY.split("{when}")[0] in screen._banner.text
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_online_data_restores_accent_add_and_enabled_row_actions() -> None:
    from market_monitor_gui.services.filters import FiltersData

    root, screen, theme = _make_screen()
    try:
        screen.render(FiltersData((_item(),), from_cache=False, cached_at=None))
        root.update()

        assert screen._add_button.cget("state") == "normal"
        assert screen._add_button.cget("fg_color") == theme.colour("accent")
        assert screen._refresh_button.cget("fg_color") == "transparent"
        assert screen._rows[1]._delete.cget("state") == "normal"
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_failed_read_locks_and_failed_write_only_reports() -> None:
    from market_monitor_gui.api.errors import ApiError, ErrorKind
    from market_monitor_gui.services.errors import text_key_for_exception
    from market_monitor_gui.services.filters import FiltersData
    from market_monitor_gui.texts import ru

    root, screen, _theme = _make_screen()
    try:
        screen.render(FiltersData((_item(),), from_cache=False, cached_at=None))
        root.update()

        screen.show_write_error(text_key_for_exception(ApiError(ErrorKind.SERVER)))
        root.update()
        assert screen._add_button.cget("state") == "normal"
        assert screen._rows[1]._delete.cget("state") == "normal"
        assert screen._banner.text == ru.ERR_SERVER

        screen.show_read_error(text_key_for_exception(ApiError(ErrorKind.NETWORK)))
        root.update()
        assert screen._add_button.cget("state") == "disabled"
        assert screen._rows[1]._delete.cget("state") == "disabled"
        assert ru.READONLY_NOTICE in screen._banner.text
    finally:
        root.destroy()
