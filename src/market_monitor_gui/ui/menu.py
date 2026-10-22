"""Application menu: a sidebar button that posts a native ``tk.Menu``.

A single click opens the menu anchored to the button and it stays open (no press
and-hold). It closes on item selection, Escape, a click outside it, or a second click
of the button - all handled by Tk's own menu machinery.

Why a native ``tk.Menu`` instead of a ``CTkToplevel`` popup: a borderless CustomTkinter
toplevel was being mapped at ``(0, 0)`` for a frame before its geometry applied (a
top-left "flash"), and ``CTkToplevel`` runs extra scaling/shadow code that can reposition
it. Tk's menu posting is atomic and battle-tested, so the button uses
``tk_popup`` (called on the button release, so the opening click never races the grab).
"""

from __future__ import annotations

import time
import tkinter as tk
from collections.abc import Callable
from enum import StrEnum
from functools import partial
from typing import Final

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme


class MenuAction(StrEnum):
    """Actions offered by the application menu."""

    CONNECTION = "connection"
    CHECK = "check"
    DISCONNECT = "disconnect"
    ABOUT = "about"


#: Menu entries in display order (label text comes from ``texts/ru.py``).
_MENU_ITEMS: Final[tuple[tuple[MenuAction, str], ...]] = (
    (MenuAction.CONNECTION, ru.MENU_CONNECTION_SETTINGS),
    (MenuAction.CHECK, ru.MENU_CHECK_CONNECTION),
    (MenuAction.DISCONNECT, ru.MENU_DISCONNECT),
    (MenuAction.ABOUT, ru.MENU_ABOUT),
)

#: Ignore a toggle request this soon after the menu was dismissed, so the click that
#: dismisses a posted menu (which is reported as "outside") never reopens it.
_REOPEN_GUARD_SECONDS: Final[float] = 0.2


class AppMenu:
    """A CustomTkinter button that posts a native menu of operator actions."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        on_action: Callable[[MenuAction], None],
    ) -> None:
        self._master = master
        self._fonts = fonts
        self._on_action = on_action
        self._unposted_at = 0.0

        self._menu = tk.Menu(master, tearoff=False)
        for action, label in _MENU_ITEMS:
            self._menu.add_command(label=label, command=partial(self._fire, action))
        self._menu.bind("<Unmap>", self._on_unmap)

        self.button = ctk.CTkButton(
            master,
            text=ru.fmt_menu_button(),
            anchor="w",
            font=fonts.body,
            border_width=1,
            border_color=theme.colour("muted"),
            **theme.secondary_button(),
            command=self.toggle,
        )
        self.button.pack(fill="x")

    # -- open / close ---------------------------------------------------------

    def toggle(self) -> None:
        """Post the menu, or unpost it if it is already shown."""
        if self._is_open():
            self.close()
            return
        if time.monotonic() - self._unposted_at < _REOPEN_GUARD_SECONDS:
            return
        self.open()

    def open(self) -> None:
        """Post the menu anchored just above the button (falling back to below)."""
        self._apply_colours()
        self._menu.update_idletasks()
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() - self._menu.winfo_reqheight()
        if y < 0:
            y = self.button.winfo_rooty() + self.button.winfo_height()
        # Atomic post at an explicit position: no intermediate (0, 0) frame, unlike a
        # toplevel that is mapped first and given its geometry afterwards.
        self._menu.tk_popup(x, y)

    def close(self) -> None:
        """Unpost the menu."""
        self._menu.unpost()

    def _is_open(self) -> bool:
        return bool(self._menu.winfo_ismapped())

    def _on_unmap(self, _event: tk.Event[tk.Misc]) -> None:
        self._unposted_at = time.monotonic()

    def _fire(self, action: MenuAction) -> None:
        self._menu.unpost()
        self._on_action(action)

    # -- styling --------------------------------------------------------------

    def _apply_colours(self) -> None:
        """Match the menu to the current light/dark appearance (colour is supplemental)."""
        index = 1 if ctk.get_appearance_mode().lower() == "dark" else 0
        self._menu.configure(
            background=theme.colour("surface")[index],
            foreground=theme.colour("text")[index],
            activebackground=theme.colour("accent")[index],
            activeforeground=theme.colour("on_accent")[index],
        )
