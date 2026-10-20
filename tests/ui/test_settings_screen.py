"""G16: the Settings form unit, borders, and focus behaviour (needs a display)."""

from __future__ import annotations

import os
from typing import Any

import pytest

pytestmark = pytest.mark.e2e


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _make_screen() -> tuple[Any, Any, Any, list[float]]:
    import customtkinter as ctk

    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.screens.settings import SettingsScreen

    root = ctk.CTk()
    saved: list[float] = []
    screen = SettingsScreen(
        root,
        fonts=theme.build_fonts(),
        on_refresh=lambda: None,
        on_save=saved.append,
    )
    screen.pack(fill="both", expand=True)
    return root, screen, theme, saved


def _online(value: float) -> Any:
    from market_monitor_gui.services.settings import SettingsData

    return SettingsData(price_drop_threshold_percent=value, from_cache=False, cached_at=None)


def _cached(value: float) -> Any:
    from datetime import UTC, datetime

    from market_monitor_gui.services.settings import SettingsData

    return SettingsData(
        price_drop_threshold_percent=value,
        from_cache=True,
        cached_at=datetime.now(UTC),
    )


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_percent_suffix_is_a_separate_label_and_the_value_stays_bare() -> None:
    import customtkinter as ctk

    from market_monitor_gui.texts import ru

    root, screen, _theme, _saved = _make_screen()
    try:
        screen.render(_online(7.5))
        root.update()

        assert screen._value.get() == "7,5"
        labels = [
            str(child.cget("text"))
            for child in screen._field_row.winfo_children()
            if isinstance(child, ctk.CTkLabel)
        ]
        assert labels == [ru.SETTINGS_PERCENT_SUFFIX]
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_hint_states_the_allowed_range() -> None:
    import customtkinter as ctk

    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui.forms import THRESHOLD_MAX, THRESHOLD_MIN
    from market_monitor_gui.ui.settings_view import format_threshold

    root, screen, _theme, _saved = _make_screen()
    try:
        root.update()
        assert format_threshold(THRESHOLD_MIN) in ru.SETTINGS_THRESHOLD_HINT
        assert format_threshold(THRESHOLD_MAX) in ru.SETTINGS_THRESHOLD_HINT

        texts = [
            str(child.cget("text"))
            for child in screen.body.winfo_children()
            if isinstance(child, ctk.CTkLabel)
        ]
        assert ru.SETTINGS_THRESHOLD_HINT in texts
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_validation_failure_marks_the_entry_and_success_restores_it() -> None:
    from market_monitor_gui.texts import ru

    root, screen, theme, saved = _make_screen()
    try:
        screen.render(_online(7.5))
        root.update()
        assert screen._entry.cget("border_color") == theme.colour("accent")

        screen._value.set("abc")
        screen._submit()
        root.update()
        assert screen._status.cget("text") == ru.SETTINGS_THRESHOLD_NOT_A_NUMBER
        assert screen._entry.cget("border_color") == theme.colour("error")
        assert saved == []

        screen._value.set("12,5")
        screen._submit()
        root.update()
        assert screen._entry.cget("border_color") == theme.colour("accent")
        assert screen._status.cget("text") == ""
        assert saved == [12.5]
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_server_write_error_keeps_the_normal_border() -> None:
    from market_monitor_gui.texts import ru

    root, screen, theme, _saved = _make_screen()
    try:
        screen.render(_online(7.5))
        root.update()

        screen.show_write_error("ERR_SERVER")
        root.update()
        assert screen._status.cget("text") == ru.ERR_SERVER
        assert screen._entry.cget("border_color") == theme.colour("accent")
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_on_show_and_online_render_request_focus(monkeypatch: pytest.MonkeyPatch) -> None:
    root, screen, _theme, _saved = _make_screen()
    try:
        calls: list[str] = []
        monkeypatch.setattr(screen._entry, "focus_set", lambda *_a, **_k: calls.append("focus"))

        screen.on_show()
        root.update()
        assert calls == ["focus"]

        screen.render(_online(7.5))
        root.update()
        assert calls == ["focus", "focus"]
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_cached_render_does_not_request_focus(monkeypatch: pytest.MonkeyPatch) -> None:
    root, screen, _theme, _saved = _make_screen()
    try:
        calls: list[str] = []
        monkeypatch.setattr(screen._entry, "focus_set", lambda *_a, **_k: calls.append("focus"))

        screen.render(_cached(7.5))
        root.update()
        assert screen._entry.cget("state") == "disabled"
        assert calls == []
    finally:
        root.destroy()
