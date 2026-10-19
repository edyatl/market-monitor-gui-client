"""Scrolling helpers for :class:`customtkinter.CTkScrollableFrame`.

CustomTkinter binds only ``<MouseWheel>`` (Windows/macOS). On X11 the wheel is delivered
as ``<Button-4>``/``<Button-5>``, so those platforms get no wheel scrolling at all. This
module adds the X11 bindings without touching ``<MouseWheel>`` (which CTk already handles,
so rebinding it would double the scroll speed on Windows).

Only public attributes are used: the event widget's ``master`` chain and each scroll area's
``master`` (which is the scroll :class:`tkinter.Canvas`).
"""

from __future__ import annotations

import sys
import tkinter as tk

import customtkinter as ctk

_WHEEL_BOUND_ATTR = "_mm_wheel_bound"


def enable_wheel_scroll(frame: ctk.CTkScrollableFrame) -> None:
    """Make ``frame`` scroll with the X11 mouse wheel (no-op on Windows/macOS).

    The binding lives on the frame's toplevel so it fires wherever the pointer is inside
    the scroll area, including over child labels and buttons. Rebinding ``<MouseWheel>`` is
    deliberately avoided because CTk already listens for it.
    """
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return
    if getattr(frame, _WHEEL_BOUND_ATTR, False):
        return
    setattr(frame, _WHEEL_BOUND_ATTR, True)

    toplevel = frame.winfo_toplevel()
    toplevel.bind("<Button-4>", lambda event: _scroll(event, -1), add="+")
    toplevel.bind("<Button-5>", lambda event: _scroll(event, 1), add="+")


def _scroll(event: tk.Event[tk.Misc], direction: int) -> None:
    frame = _scrollable_ancestor(event.widget)
    canvas = getattr(frame, "master", None) if frame is not None else None
    if not isinstance(canvas, tk.Canvas):
        return
    if canvas.yview() == (0.0, 1.0):
        return
    canvas.yview("scroll", direction, "units")


def _scrollable_ancestor(widget: tk.Misc | None) -> ctk.CTkScrollableFrame | None:
    """Return the nearest enclosing scroll area, or ``None`` when not inside one."""
    while widget is not None:
        if isinstance(widget, ctk.CTkScrollableFrame):
            return widget
        widget = getattr(widget, "master", None)
    return None
