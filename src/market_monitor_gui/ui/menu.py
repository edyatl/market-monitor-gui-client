"""Application menu: a sidebar button opening a native popup menu."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from enum import StrEnum

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme


class MenuAction(StrEnum):
    """Actions offered by the application menu."""

    CONNECTION = "connection"
    CHECK = "check"
    LOGOUT = "logout"
    ABOUT = "about"


class AppMenu:
    """A CustomTkinter button that pops a ``tkinter.Menu`` of operator actions."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        on_action: Callable[[MenuAction], None],
    ) -> None:
        self._on_action = on_action

        self._menu = tk.Menu(master, tearoff=False)
        self._menu.add_command(
            label=ru.MENU_CONNECTION_SETTINGS,
            command=lambda: self._fire(MenuAction.CONNECTION),
        )
        self._menu.add_command(
            label=ru.MENU_CHECK_CONNECTION,
            command=lambda: self._fire(MenuAction.CHECK),
        )
        self._menu.add_separator()
        self._menu.add_command(label=ru.MENU_LOGOUT, command=lambda: self._fire(MenuAction.LOGOUT))
        self._menu.add_separator()
        self._menu.add_command(label=ru.MENU_ABOUT, command=lambda: self._fire(MenuAction.ABOUT))

        self.button = ctk.CTkButton(
            master, text=ru.MENU_BUTTON, font=fonts.body, command=self.popup
        )
        self.button.pack(fill="x")

    def _fire(self, action: MenuAction) -> None:
        self._on_action(action)

    def popup(self) -> None:
        x = int(self.button.winfo_rootx())
        y = int(self.button.winfo_rooty())
        try:
            self._menu.tk_popup(x, y)
        finally:
            self._menu.grab_release()
