"""Connection settings dialog: edit the API origin and optionally save the secret."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.dialogs.base import BaseDialog
from market_monitor_gui.ui.forms import custom_origin_warning, validate_origin_input


class ConnectionDialog(BaseDialog):
    """Validate the origin inline; the shell persists and acts on save."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        fonts: theme.Fonts,
        initial_origin: str,
        on_save: Callable[[str, str | None, bool], None],
        on_check: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(master, title=ru.CONN_TITLE, fonts=fonts, resizable=True)
        self._on_save = on_save
        self._on_check = on_check
        self._origin = tk.StringVar(value=initial_origin)
        self._secret = tk.StringVar()
        self._save_secret = tk.BooleanVar(value=False)
        self._build()
        self._refresh_warning()

    @property
    def origin(self) -> str:
        return self._origin.get()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text=ru.CONN_ORIGIN_LABEL,
            font=self.fonts.body,
            anchor="w",
        ).pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_L, theme.PAD_XS))
        self._origin_entry = ctk.CTkEntry(self, textvariable=self._origin, width=460)
        self._origin_entry.pack(fill="x", padx=theme.PAD_L)
        self._origin_entry.bind("<KeyRelease>", self._on_edit)

        ctk.CTkLabel(
            self,
            text=ru.CONN_ORIGIN_HELP,
            font=self.fonts.small,
            wraplength=460,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_XS, theme.PAD_XS))

        self._warning = ctk.CTkLabel(
            self,
            text="",
            font=self.fonts.small,
            text_color=theme.colour("warn"),
            wraplength=460,
            justify="left",
            anchor="w",
        )
        self._warning.pack(fill="x", padx=theme.PAD_L)

        ctk.CTkLabel(
            self,
            text=ru.CONN_SECRET_LABEL,
            font=self.fonts.body,
            anchor="w",
        ).pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_M, theme.PAD_XS))
        self._secret_entry = ctk.CTkEntry(self, textvariable=self._secret, show="*", width=460)
        self._secret_entry.pack(fill="x", padx=theme.PAD_L)

        self._save_secret_box = ctk.CTkCheckBox(
            self,
            text=ru.CONN_SAVE_SECRET,
            variable=self._save_secret,
            font=self.fonts.body,
        )
        self._save_secret_box.pack(fill="x", padx=theme.PAD_L, pady=theme.PAD_S)

        self._error = ctk.CTkLabel(
            self,
            text="",
            font=self.fonts.small,
            text_color=theme.colour("error"),
            anchor="w",
        )
        self._error.pack(fill="x", padx=theme.PAD_L)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=theme.PAD_L, pady=theme.PAD_L)

        self._save_button = ctk.CTkButton(buttons, text=ru.ACTION_SAVE, command=self._save)
        self._save_button.pack(side="left")
        if self._on_check is not None:
            ctk.CTkButton(
                buttons,
                text=ru.MENU_CHECK_CONNECTION,
                fg_color="transparent",
                hover_color=theme.colour("muted"),
                command=self._check,
            ).pack(side="left", padx=theme.PAD_S)
        ctk.CTkButton(
            buttons,
            text=ru.ACTION_CANCEL,
            fg_color="transparent",
            hover_color=theme.colour("muted"),
            command=self.close,
        ).pack(side="left")

        self.after(50, self._origin_entry.focus_set)

    def _on_edit(self, _event: object) -> None:
        self._error.configure(text="")
        self._refresh_warning()

    def _refresh_warning(self) -> None:
        result = validate_origin_input(self._origin.get())
        messages = [key for key in (result.warning,) if key]
        if result.origin is not None:
            custom = custom_origin_warning(result.origin)
            if custom is not None:
                messages.append(custom)
        self._warning.configure(text=" ".join(ru.text_for(key) for key in messages))

    def _save(self) -> None:
        result = validate_origin_input(self._origin.get())
        if result.origin is None or result.error is not None:
            self._error.configure(text=ru.text_for(ru.CONN_ORIGIN_INVALID))
            return
        secret = self._secret.get().strip() or None
        self._on_save(result.origin, secret, bool(self._save_secret.get()))

    def _check(self) -> None:
        if self._on_check is None:
            return
        result = validate_origin_input(self._origin.get())
        if result.origin is None or result.error is not None:
            self._error.configure(text=ru.text_for(ru.CONN_ORIGIN_INVALID))
            return
        self._on_check(result.origin)

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self._save_button.configure(state=state)
        self._origin_entry.configure(state=state)
        self._secret_entry.configure(state=state)

    def show_error(self, text_key: str) -> None:
        self._error.configure(text=ru.text_for(text_key))

    def show_info(self, text_key: str) -> None:
        self._error.configure(text=ru.text_for(text_key))

    def clear_secret(self) -> None:
        self._secret.set("")
