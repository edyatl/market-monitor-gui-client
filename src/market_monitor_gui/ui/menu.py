"""Application menu: a sidebar button that toggles a CustomTkinter popup.

A single click opens the popup and it stays open (no press-and-hold). It closes when an
item is chosen, when Escape is pressed, or when the operator clicks anywhere else. The
popup is a borderless :class:`CTkToplevel` (not a native ``tk.Menu``) so the toggle
behaviour is fully under our control and matches CustomTkinter's own widgets.
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Callable
from enum import StrEnum
from typing import Final

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme


class MenuAction(StrEnum):
    """Actions offered by the application menu."""

    CONNECTION = "connection"
    CHECK = "check"
    LOGOUT = "logout"
    ABOUT = "about"


#: Menu entries in display order (label text comes from ``texts/ru.py``).
_MENU_ITEMS: Final[tuple[tuple[MenuAction, str], ...]] = (
    (MenuAction.CONNECTION, ru.MENU_CONNECTION_SETTINGS),
    (MenuAction.CHECK, ru.MENU_CHECK_CONNECTION),
    (MenuAction.LOGOUT, ru.MENU_LOGOUT),
    (MenuAction.ABOUT, ru.MENU_ABOUT),
)

_ITEM_HEIGHT: Final[int] = 34


class AppMenu:
    """A CustomTkinter button that toggles a persistent popup of operator actions."""

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
        self._popup: ctk.CTkToplevel | None = None
        self._press_while_open = False
        self._suppress_toggle = False

        self.button = ctk.CTkButton(
            master,
            text=ru.MENU_BUTTON,
            font=fonts.body,
            **theme.secondary_button(),
            command=self.toggle,
        )
        self.button.pack(fill="x")
        # Widget-level press runs before the "all" binding, letting us tell a click on
        # this button (which should toggle) apart from a click elsewhere (which dismisses).
        self.button.bind("<ButtonPress-1>", self._record_press, add="+")
        master.winfo_toplevel().bind_all("<Button-1>", self._on_any_click, add="+")

    # -- open / close ---------------------------------------------------------

    def toggle(self) -> None:
        """Open the menu, or close it if it is already open."""
        if self._suppress_toggle:
            self._suppress_toggle = False
            return
        if self._is_open():
            self.close()
        else:
            self.open()

    def open(self) -> None:
        """Show the popup above the button and keep it open until dismissed."""
        if self._is_open():
            return
        popup = ctk.CTkToplevel(self._master)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        self._popup = popup
        for action, label in _MENU_ITEMS:
            ctk.CTkButton(
                popup,
                text=label,
                anchor="w",
                height=_ITEM_HEIGHT,
                corner_radius=0,
                font=self._fonts.body,
                **theme.secondary_button(),
                command=lambda selected=action: self._select(selected),
            ).pack(fill="x")
        popup.bind("<Escape>", lambda _event: self.close())
        popup.update_idletasks()
        width = max(popup.winfo_reqwidth(), self.button.winfo_width())
        height = popup.winfo_reqheight()
        x = self.button.winfo_rootx()
        y = max(self.button.winfo_rooty() - height, 0)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.lift()
        popup.focus_force()

    def close(self) -> None:
        """Destroy the popup if it exists."""
        popup = self._popup
        self._popup = None
        if popup is not None and popup.winfo_exists():
            popup.destroy()

    def _select(self, action: MenuAction) -> None:
        self.close()
        self._on_action(action)

    def _is_open(self) -> bool:
        return self._popup is not None and bool(self._popup.winfo_exists())

    # -- dismissal ------------------------------------------------------------

    def _record_press(self, _event: tk.Event[tk.Misc]) -> None:
        self._press_while_open = self._is_open()

    def _on_any_click(self, event: tk.Event[tk.Misc]) -> None:
        if not self._is_open():
            return
        popup = self._popup
        widget = event.widget
        if popup is not None and widget is not None:
            with contextlib.suppress(tk.TclError):
                if widget.winfo_toplevel() is popup:
                    return
        # A press on the menu button closes the menu; suppress the release that follows
        # so the button's toggle does not immediately reopen it.
        self._suppress_toggle = self._press_while_open
        self.close()
