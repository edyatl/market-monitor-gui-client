"""Login dialog: enter the shared application secret and sign in."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.controls import set_button_enabled
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
        ).pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.CONTENT_GUTTER, theme.SECTION_GAP))

        ctk.CTkLabel(self, text=ru.LOGIN_SECRET_LABEL, font=self.fonts.body, anchor="w").pack(
            fill="x", padx=theme.CONTENT_GUTTER
        )
        self._entry = ctk.CTkEntry(self, textvariable=self._secret, show="*", width=420)
        self._entry.pack(
            fill="x",
            padx=theme.CONTENT_GUTTER,
            pady=(theme.FIELD_GAP, theme.FIELD_BOTTOM),
        )

        self._error = ctk.CTkLabel(self, text="", font=self.fonts.small, anchor="w")
        self._error.pack(fill="x", padx=theme.CONTENT_GUTTER)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=theme.CONTENT_GUTTER, pady=theme.CONTENT_GUTTER)

        self._login_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_LOGIN,
            command=self._submit,
            **theme.primary_button(),
        )
        self._login_button.pack(side="left")
        ctk.CTkButton(
            buttons,
            text=ru.ACTION_CANCEL,
            command=self.close,
            **theme.secondary_button(),
        ).pack(side="left", padx=theme.TOOLBAR_GAP)
        if self._on_open_connection is not None:
            ctk.CTkButton(
                buttons,
                text=ru.MENU_CONNECTION_SETTINGS,
                command=self._open_connection,
                **theme.secondary_button(),
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
            self.show_error("ERR_SECRET_REQUIRED")
            return
        self.set_busy(True)
        self._on_submit(secret)

    def set_busy(self, busy: bool) -> None:
        """Disable the input while the shell performs the login."""
        self._entry.configure(state="disabled" if busy else "normal")
        set_button_enabled(self._login_button, not busy, theme.primary_button())
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
