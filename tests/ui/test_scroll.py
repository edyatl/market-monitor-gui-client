"""G13: X11 mouse-wheel scrolling for ``CTkScrollableFrame`` (needs a display)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_wheel_scrolls_the_enclosing_area() -> None:
    import customtkinter as ctk

    from market_monitor_gui.ui.scroll import enable_wheel_scroll

    root = ctk.CTk()
    try:
        frame = ctk.CTkScrollableFrame(root, width=240, height=120)
        frame.pack()
        for index in range(60):
            ctk.CTkLabel(frame, text=f"row {index}").pack(fill="x")
        root.update()

        canvas = frame.master
        assert canvas.yview()[0] < 1.0, "test content must overflow the viewport"

        enable_wheel_scroll(frame)
        child = frame.winfo_children()[0]

        child.event_generate("<Button-5>", when="now")
        root.update()
        scrolled_down = canvas.yview()[0]
        assert scrolled_down > 0.0

        child.event_generate("<Button-4>", when="now")
        root.update()
        assert canvas.yview()[0] < scrolled_down
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_wheel_outside_the_area_does_not_scroll_it() -> None:
    import customtkinter as ctk

    from market_monitor_gui.ui.scroll import enable_wheel_scroll

    root = ctk.CTk()
    try:
        frame = ctk.CTkScrollableFrame(root, width=240, height=120)
        frame.pack()
        for index in range(60):
            ctk.CTkLabel(frame, text=f"row {index}").pack(fill="x")
        outside = ctk.CTkLabel(root, text="outside")
        outside.pack()
        root.update()

        canvas = frame.master
        enable_wheel_scroll(frame)

        inside = frame.winfo_children()[0]
        inside.event_generate("<Button-5>", when="now")
        root.update()
        after_inside = canvas.yview()[0]
        assert after_inside > 0.0

        outside.event_generate("<Button-5>", when="now")
        root.update()
        assert canvas.yview()[0] == after_inside
    finally:
        root.destroy()


@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_enable_wheel_scroll_is_idempotent() -> None:
    import customtkinter as ctk

    from market_monitor_gui.ui.scroll import enable_wheel_scroll

    root = ctk.CTk()
    try:
        frame = ctk.CTkScrollableFrame(root, width=240, height=120)
        frame.pack()
        enable_wheel_scroll(frame)
        enable_wheel_scroll(frame)
        assert frame._mm_wheel_bound is True
    finally:
        root.destroy()
