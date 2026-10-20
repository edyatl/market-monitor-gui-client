"""Auth screen shown in the content area when there is no active session."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.screens.base import ScreenFrame


class AuthScreen(ScreenFrame):
    """Prompts the operator to sign in; the login dialog is opened by the shell."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        on_login: Callable[[], None],
    ) -> None:
        super().__init__(master, title=ru.LOGIN_TITLE, fonts=fonts)
        ctk.CTkLabel(
            self.body,
            text=ru.LOGIN_HELP,
            font=fonts.body,
            wraplength=640,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, theme.SECTION_GAP))
        ctk.CTkButton(
            self.body,
            text=ru.ACTION_LOGIN,
            command=on_login,
            **theme.primary_button(),
        ).pack(anchor="w")
