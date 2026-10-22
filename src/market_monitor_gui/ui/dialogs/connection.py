"""Connection settings dialog: edit the API origin and manage the stored secret.

This is the single place that manages the application secret: it shows whether a secret
is stored (a masked placeholder, never the value), lets the operator replace it, keep it,
or delete it (the forget-secret action), and warns when a development ``APP_SECRET``
override is active. Validation is inline; the shell persists and acts on save.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.controls import set_button_enabled
from market_monitor_gui.ui.dialogs.base import BaseDialog
from market_monitor_gui.ui.forms import (
    ConnectionFormValues,
    custom_origin_warning,
    validate_origin_input,
)


class ConnectionDialog(BaseDialog):
    """Validate the origin inline; the shell persists and acts on save."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        fonts: theme.Fonts,
        initial_origin: str,
        secret_saved: bool,
        env_secret: bool = False,
        on_save: Callable[[ConnectionFormValues], None],
        on_check: Callable[[str], None] | None = None,
        on_forget: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, title=ru.CONN_TITLE, fonts=fonts, resizable=True)
        self._on_save = on_save
        self._on_check = on_check
        self._on_forget = on_forget
        self._secret_saved = secret_saved
        self._origin = tk.StringVar(value=initial_origin)
        self._secret = tk.StringVar()
        self._save_secret = tk.BooleanVar(value=secret_saved)
        self._build(env_secret)
        self._refresh_warning()

    @property
    def origin(self) -> str:
        return self._origin.get()

    def _build(self, env_secret: bool) -> None:
        ctk.CTkLabel(
            self,
            text=ru.CONN_ORIGIN_LABEL,
            font=self.fonts.body,
            anchor="w",
        ).pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.CONTENT_GUTTER, theme.FIELD_GAP))
        self._origin_entry = ctk.CTkEntry(self, textvariable=self._origin, width=460)
        self._origin_entry.pack(fill="x", padx=theme.CONTENT_GUTTER)
        self._origin_entry.bind("<KeyRelease>", self._on_edit)

        ctk.CTkLabel(
            self,
            text=ru.CONN_ORIGIN_HELP,
            font=self.fonts.small,
            wraplength=460,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.FIELD_GAP, theme.FIELD_BOTTOM))

        self._warning = ctk.CTkLabel(
            self,
            text="",
            font=self.fonts.small,
            text_color=theme.colour("warn"),
            wraplength=460,
            justify="left",
            anchor="w",
        )
        self._warning.pack(fill="x", padx=theme.CONTENT_GUTTER)

        ctk.CTkLabel(
            self,
            text=ru.CONN_SECRET_LABEL,
            font=self.fonts.body,
            anchor="w",
        ).pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.SECTION_GAP, theme.FIELD_GAP))
        self._secret_entry = ctk.CTkEntry(
            self,
            textvariable=self._secret,
            show="*",
            width=460,
            placeholder_text=self._placeholder_text(),
        )
        self._secret_entry.pack(fill="x", padx=theme.CONTENT_GUTTER)

        self._secret_state = ctk.CTkLabel(
            self,
            text=self._state_text(),
            font=self.fonts.small,
            text_color=self._state_colour(),
            anchor="w",
        )
        self._secret_state.pack(
            fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.FIELD_GAP, theme.FIELD_GAP)
        )

        if env_secret:
            ctk.CTkLabel(
                self,
                text=ru.CONN_SECRET_ENV_NOTE,
                font=self.fonts.small,
                text_color=theme.colour("warn"),
                wraplength=460,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(0, theme.FIELD_GAP))

        self._save_secret_box = ctk.CTkCheckBox(
            self,
            text=ru.CONN_SAVE_SECRET,
            variable=self._save_secret,
            font=self.fonts.body,
        )
        self._save_secret_box.pack(fill="x", padx=theme.CONTENT_GUTTER, pady=theme.BANNER_BOTTOM)

        ctk.CTkLabel(
            self,
            text=ru.CONN_SECRET_HELP,
            font=self.fonts.small,
            text_color=theme.colour("muted"),
            wraplength=460,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(0, theme.FIELD_GAP))

        self._forget_button = ctk.CTkButton(
            self,
            text=ru.ACTION_FORGET_SECRET,
            command=self._forget,
            **theme.secondary_button(),
        )
        self._forget_button.pack(
            anchor="w", padx=theme.CONTENT_GUTTER, pady=(0, theme.FIELD_BOTTOM)
        )

        self._error = ctk.CTkLabel(
            self,
            text="",
            font=self.fonts.small,
            text_color=theme.colour("error"),
            wraplength=460,
            justify="left",
            anchor="w",
        )
        self._error.pack(fill="x", padx=theme.CONTENT_GUTTER)

        self._check_label = ctk.CTkLabel(
            self,
            text="",
            font=self.fonts.small,
            wraplength=460,
            justify="left",
            anchor="w",
        )
        self._check_label.pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.FIELD_GAP, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=theme.CONTENT_GUTTER, pady=theme.CONTENT_GUTTER)

        self._save_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_SAVE,
            command=self._save,
            **theme.primary_button(),
        )
        self._save_button.pack(side="left")
        self._check_button: ctk.CTkButton | None = None
        if self._on_check is not None:
            self._check_button = ctk.CTkButton(
                buttons,
                text=ru.MENU_CHECK_CONNECTION,
                command=self._check,
                **theme.secondary_button(),
            )
            self._check_button.pack(side="left", padx=theme.TOOLBAR_GAP)
        ctk.CTkButton(
            buttons,
            text=ru.ACTION_CANCEL,
            command=self.close,
            **theme.secondary_button(),
        ).pack(side="left")

        self._apply_secret_state()
        self.after(50, self._origin_entry.focus_set)

    # -- secret state ----------------------------------------------------------

    def _placeholder_text(self) -> str:
        return ru.CONN_SECRET_PLACEHOLDER if self._secret_saved else ""

    def _state_text(self) -> str:
        return ru.CONN_SECRET_SAVED if self._secret_saved else ru.CONN_SECRET_NOT_SAVED

    def _state_colour(self) -> str | tuple[str, str]:
        return theme.colour("ok") if self._secret_saved else theme.colour("muted")

    def _apply_secret_state(self) -> None:
        self._secret_entry.configure(placeholder_text=self._placeholder_text())
        self._secret_state.configure(text=self._state_text(), text_color=self._state_colour())
        set_button_enabled(self._forget_button, self._secret_saved, theme.secondary_button())

    def set_secret_saved(self, saved: bool) -> None:
        """Reflect the store after a delete (or a save) performed by the shell."""
        self._secret_saved = saved
        self._save_secret.set(saved)
        self._secret.set("")
        self._apply_secret_state()

    # -- validation ------------------------------------------------------------

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

    # -- actions ---------------------------------------------------------------

    def _save(self) -> None:
        result = validate_origin_input(self._origin.get())
        if result.origin is None or result.error is not None:
            self._error.configure(text=ru.text_for("CONN_ORIGIN_INVALID"))
            return
        values = ConnectionFormValues(
            origin=result.origin,
            secret=self._secret.get().strip() or None,
            remember=bool(self._save_secret.get()),
        )
        self._on_save(values)

    def _forget(self) -> None:
        if self._on_forget is not None and self._secret_saved:
            self._on_forget()

    def _check(self) -> None:
        if self._on_check is None:
            return
        result = validate_origin_input(self._origin.get())
        if result.origin is None or result.error is not None:
            self._error.configure(text=ru.text_for("CONN_ORIGIN_INVALID"))
            return
        self.show_checking()
        self._on_check(result.origin)

    # -- state from the shell --------------------------------------------------

    def show_checking(self) -> None:
        """Indicate that a connection check is running."""
        self._check_label.configure(text=ru.CHECK_IN_PROGRESS, text_color=theme.colour("muted"))

    def show_check_result(self, ok: bool, text: str) -> None:
        """Show the outcome of a connection check inline (never a silent no-op)."""
        self._check_label.configure(
            text=text,
            text_color=theme.colour("ok") if ok else theme.colour("error"),
        )

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        set_button_enabled(self._save_button, not busy, theme.primary_button())
        self._origin_entry.configure(state=state)
        self._secret_entry.configure(state=state)
        set_button_enabled(
            self._forget_button, not busy and self._secret_saved, theme.secondary_button()
        )
        if self._check_button is not None:
            set_button_enabled(self._check_button, not busy, theme.secondary_button())

    def show_error(self, text_key: str) -> None:
        self._error.configure(text=ru.text_for(text_key))

    def show_info(self, text_key: str) -> None:
        self._error.configure(text=ru.text_for(text_key))

    def clear_secret(self) -> None:
        self._secret.set("")
