"""Login dialog: enter the shared application secret and sign in."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.dialogs.base import BaseDialog


class LoginDialog(BaseDialog):
    """Collects the secret. The shell performs the login and reports back."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        fonts: theme.Fonts,
        on_submit: Callable[[str], None],
        on_open_connection: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, title=ru.LOGIN_TITLE, fonts=fonts)
        self._on_submit = on_submit
        self._on_open_connection = on_open_connection
        self._secret = tk.StringVar()
        self._build()
        self.bind("<Return>", self._on_return)

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text=ru.LOGIN_HELP,
            font=self.fonts.body,
            wraplength=420,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_L, theme.PAD_M))

        ctk.CTkLabel(self, text=ru.LOGIN_SECRET_LABEL, font=self.fonts.body, anchor="w").pack(
            fill="x", padx=theme.PAD_L
        )
        self._entry = ctk.CTkEntry(self, textvariable=self._secret, show="*", width=420)
        self._entry.pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_XS, theme.PAD_S))

        self._error = ctk.CTkLabel(self, text="", font=self.fonts.small, anchor="w")
        self._error.pack(fill="x", padx=theme.PAD_L)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=theme.PAD_L, pady=theme.PAD_L)

        self._login_button = ctk.CTkButton(buttons, text=ru.ACTION_LOGIN, command=self._submit)
        self._login_button.pack(side="left")
        ctk.CTkButton(
            buttons,
            text=ru.ACTION_CANCEL,
            fg_color="transparent",
            hover_color=theme.colour("muted"),
            command=self.close,
        ).pack(side="left", padx=theme.PAD_S)
        if self._on_open_connection is not None:
            ctk.CTkButton(
                buttons,
                text=ru.MENU_CONNECTION_SETTINGS,
                fg_color="transparent",
                hover_color=theme.colour("muted"),
                command=self._open_connection,
            ).pack(side="right")

        self.after(50, self._entry.focus_set)

    def _on_return(self, _event: object) -> None:
        self._submit()

    def _open_connection(self) -> None:
        if self._on_open_connection is not None:
            self._on_open_connection()

    def _submit(self) -> None:
        secret = self._secret.get()
        if not secret.strip():
            self.show_error(ru.ERR_SECRET_REQUIRED)
            return
        self.set_busy(True)
        self._on_submit(secret)

    def set_busy(self, busy: bool) -> None:
        """Disable the input while the shell performs the login."""
        state = "normal" if not busy else "disabled"
        self._entry.configure(state=state)
        self._login_button.configure(state=state)
        self._error.configure(text=ru.LOGIN_IN_PROGRESS if busy else "")

    def show_error(self, text_key: str) -> None:
        """Show a Russian error and clear the (never-echoed) secret field."""
        self.set_busy(False)
        self._error.configure(text=ru.text_for(text_key))
        self._secret.set("")
        self._entry.focus_set()

    def show_success(self) -> None:
        self._error.configure(text=ru.LOGIN_SUCCESS)

    def clear_secret(self) -> None:
        self._secret.set("")
