"""Filter editor dialog: add an exclusion phrase.

Add-only: the API contract exposes no filter update endpoint, so there is no edit
mode. The shell performs the write and reports back.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.controls import set_button_enabled
from market_monitor_gui.ui.dialogs.base import BaseDialog
from market_monitor_gui.ui.forms import FilterFormValues, validate_filter_form


class FilterEditorDialog(BaseDialog):
    """Collects an exclusion phrase; the shell performs the write."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        fonts: theme.Fonts,
        on_submit: Callable[[FilterFormValues], None],
    ) -> None:
        super().__init__(master, title=ru.FILTER_EDITOR_TITLE_ADD, fonts=fonts)
        self._on_submit = on_submit
        self._phrase_var = tk.StringVar()
        self._build()
        self.bind("<Return>", self._on_return)

    def _build(self) -> None:
        ctk.CTkLabel(self, text=ru.FILTER_PHRASE_LABEL, font=self.fonts.body, anchor="w").pack(
            fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.CONTENT_GUTTER, theme.FIELD_GAP)
        )
        self._phrase_entry = ctk.CTkEntry(self, textvariable=self._phrase_var, width=440)
        self._phrase_entry.pack(fill="x", padx=theme.CONTENT_GUTTER)

        ctk.CTkLabel(
            self,
            text=ru.FILTER_PHRASE_HINT,
            font=self.fonts.small,
            text_color=theme.colour("muted"),
            wraplength=440,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.FIELD_GAP, 0))

        self._error = ctk.CTkLabel(
            self,
            text="",
            font=self.fonts.small,
            text_color=theme.colour("error"),
            wraplength=440,
            justify="left",
            anchor="w",
        )
        self._error.pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.BANNER_BOTTOM, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=theme.CONTENT_GUTTER, pady=theme.CONTENT_GUTTER)
        self._save_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_SAVE,
            command=self._submit,
            **theme.primary_button(),
        )
        self._save_button.pack(side="left")
        ctk.CTkButton(
            buttons,
            text=ru.ACTION_CANCEL,
            command=self.close,
            **theme.secondary_button(),
        ).pack(side="left", padx=theme.TOOLBAR_GAP)

        self.after(50, self._phrase_entry.focus_set)

    def _on_return(self, _event: object) -> None:
        self._submit()

    def _submit(self) -> None:
        result = validate_filter_form(self._phrase_var.get())
        if result.values is None:
            self._error.configure(text=ru.text_for(result.error or "ERR_VALIDATION"))
            return
        self._error.configure(text="")
        self.set_busy(True)
        self._on_submit(result.values)

    def set_busy(self, busy: bool) -> None:
        """Disable only this dialog's controls while a write is in flight."""
        self._phrase_entry.configure(state="disabled" if busy else "normal")
        set_button_enabled(self._save_button, not busy, theme.primary_button())

    def show_error(self, text_key: str) -> None:
        """Show a Russian error at the top of the form and re-enable editing."""
        self.set_busy(False)
        self._error.configure(text=ru.text_for(text_key))
