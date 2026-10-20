"""Enable/disable helpers for role-styled widgets.

Centralising the decision and the look keeps a disabled button from retaining an accent
fill with an unreadable label, and keeps busy/read-only precedence in one place.
"""

from __future__ import annotations

import customtkinter as ctk

from market_monitor_gui.ui import theme


def button_state(*, busy: bool = False, read_only: bool = False) -> str:
    """Return the tkinter state for a control affected by a mutation or offline data."""
    return "disabled" if busy or read_only else "normal"


def set_button_enabled(button: ctk.CTkButton, enabled: bool, role: dict[str, object]) -> None:
    """Enable a button with its role look, or disable it with the muted look."""
    if enabled:
        button.configure(**role, state="normal")
    else:
        button.configure(**theme.disabled_button(), state="disabled")
