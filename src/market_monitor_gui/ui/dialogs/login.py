"""Login dialog: enter the shared application secret and sign in.

Two modes share one dialog:

- **stored** — a secret is already saved on this computer, so the sign-in action reuses
  it and the operator only sees a status line; the alternate action switches to manual
  entry;
- **manual** — the secret field plus the "keep it on this computer" checkbox (checked by
  default; the shell stores the secret only after a successful login).

The shell performs the login and reports back; a rejected stored secret flips the dialog
to manual mode so the operator can type a new one.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.controls import set_button_enabled
from market_monitor_gui.ui.dialogs.base import BaseDialog
from market_monitor_gui.ui.forms import LoginFormValues


class LoginDialog(BaseDialog):
    """Collects the secret (or reuses the stored one). The shell signs in."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        fonts: theme.Fonts,
        on_submit: Callable[[LoginFormValues], None],
        on_open_connection: Callable[[], None] | None = None,
        secret_available: bool = False,
    ) -> None:
        super().__init__(master, title=ru.LOGIN_TITLE, fonts=fonts)
        self._on_submit = on_submit
        self._on_open_connection = on_open_connection
        self._secret = tk.StringVar()
        self._remember = tk.BooleanVar(value=True)
        self._manual = not secret_available
        self._build()
        self._apply_mode()
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

        self._stored_label = ctk.CTkLabel(
            self,
            text=ru.LOGIN_STORED_SECRET,
            font=self.fonts.body,
            text_color=theme.colour("ok"),
            wraplength=420,
            justify="left",
            anchor="w",
        )

        self._secret_label = ctk.CTkLabel(
            self, text=ru.LOGIN_SECRET_LABEL, font=self.fonts.body, anchor="w"
        )
        self._entry = ctk.CTkEntry(self, textvariable=self._secret, show="*", width=420)
        self._remember_box = ctk.CTkCheckBox(
            self,
            text=ru.LOGIN_REMEMBER,
            variable=self._remember,
            font=self.fonts.body,
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
        self._other_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_USE_OTHER_SECRET,
            command=self._use_other_secret,
            **theme.secondary_button(),
        )
        if self._on_open_connection is not None:
            ctk.CTkButton(
                buttons,
                text=ru.MENU_CONNECTION_SETTINGS,
                command=self._open_connection,
                **theme.secondary_button(),
            ).pack(side="right")

    # -- mode ------------------------------------------------------------------

    def _apply_mode(self) -> None:
        """Show either the stored-secret status or the manual entry widgets."""
        if self._manual:
            self._stored_label.pack_forget()
            self._other_button.pack_forget()
            self._secret_label.pack(fill="x", padx=theme.CONTENT_GUTTER)
            self._entry.pack(
                fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.FIELD_GAP, theme.FIELD_BOTTOM)
            )
            self._remember_box.pack(
                fill="x", padx=theme.CONTENT_GUTTER, pady=(0, theme.FIELD_BOTTOM)
            )
            self.after(50, self._entry.focus_set)
        else:
            self._secret_label.pack_forget()
            self._entry.pack_forget()
            self._remember_box.pack_forget()
            self._stored_label.pack(
                fill="x", padx=theme.CONTENT_GUTTER, pady=(0, theme.SECTION_GAP)
            )
            self._other_button.pack(side="left", padx=theme.TOOLBAR_GAP)
            self.after(50, self._login_button.focus_set)

    def _use_other_secret(self) -> None:
        """Switch from the stored secret to manual entry."""
        self._manual = True
        self._error.configure(text="")
        self._apply_mode()

    # -- callbacks -------------------------------------------------------------

    def _on_return(self, _event: object) -> None:
        self._submit()

    def _open_connection(self) -> None:
        if self._on_open_connection is not None:
            self._on_open_connection()

    def _submit(self) -> None:
        if not self._manual:
            self.set_busy(True)
            self._on_submit(LoginFormValues(secret=None, remember=False))
            return
        secret = self._secret.get().strip()
        if not secret:
            self.show_error("ERR_SECRET_REQUIRED")
            return
        self.set_busy(True)
        self._on_submit(LoginFormValues(secret=secret, remember=bool(self._remember.get())))

    def set_busy(self, busy: bool) -> None:
        """Disable the input while the shell performs the login."""
        self._entry.configure(state="disabled" if busy else "normal")
        set_button_enabled(self._login_button, not busy, theme.primary_button())
        set_button_enabled(self._other_button, not busy, theme.secondary_button())
        self._error.configure(text=ru.LOGIN_IN_PROGRESS if busy else "")

    def show_error(self, text_key: str) -> None:
        """Show a Russian error, switching to manual entry (never echo the secret)."""
        if not self._manual:
            self._manual = True
            self._apply_mode()
        self.set_busy(False)
        self._error.configure(text=ru.text_for(text_key))
        self._secret.set("")
        self._entry.focus_set()

    def show_success(self) -> None:
        self._error.configure(text=ru.LOGIN_SUCCESS)

    def clear_secret(self) -> None:
        self._secret.set("")
