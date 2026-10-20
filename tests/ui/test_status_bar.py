"""G15: typed transient messages in the status bar."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.unit


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def test_every_message_kind_has_a_style_and_a_ttl() -> None:
    from market_monitor_gui.ui.status_bar import (
        _MESSAGE_STYLES,
        MESSAGE_TTL_MS,
        MessageKind,
    )

    assert set(_MESSAGE_STYLES) == set(MessageKind)
    assert set(MESSAGE_TTL_MS) == set(MessageKind)


def test_errors_linger_longer_than_success() -> None:
    from market_monitor_gui.ui.status_bar import MESSAGE_TTL_MS, MessageKind

    assert MESSAGE_TTL_MS[MessageKind.SUCCESS] <= MESSAGE_TTL_MS[MessageKind.WARN]
    assert MESSAGE_TTL_MS[MessageKind.WARN] <= MESSAGE_TTL_MS[MessageKind.ERROR]
    assert MESSAGE_TTL_MS[MessageKind.ERROR] > MESSAGE_TTL_MS[MessageKind.INFO]


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_set_message_renders_kind_glyph_and_clears() -> None:
    import customtkinter as ctk

    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.status_bar import MessageKind, StatusBar

    root = ctk.CTk()
    try:
        bar = StatusBar(root, fonts=theme.build_fonts())
        root.update()

        bar.set_message("done", MessageKind.SUCCESS)
        root.update()
        assert bar._info_label.cget("text") == f"{ru.MSG_GLYPH_SUCCESS} done"
        assert bar._info_label.cget("text_color") == theme.colour("ok")

        bar.set_message("failed", MessageKind.ERROR)
        root.update()
        assert bar._info_label.cget("text") == f"{ru.MSG_GLYPH_ERROR} failed"
        assert bar._info_label.cget("text_color") == theme.colour("error")

        bar.set_message(None)
        root.update()
        assert bar._info_label.cget("text") == ""
    finally:
        root.destroy()
