"""Group editor dialog: add or edit a group's fields."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.dialogs.base import BaseDialog
from market_monitor_gui.ui.forms import GroupFormValues, validate_group_form


class GroupEditorDialog(BaseDialog):
    """Collects group fields; the shell performs the write and reports back."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        fonts: theme.Fonts,
        title: str,
        initial: GroupFormValues | None,
        on_submit: Callable[[GroupFormValues], None],
    ) -> None:
        super().__init__(master, title=title, fonts=fonts)
        self._on_submit = on_submit
        self._name_var = tk.StringVar(value=initial.name if initial else "")
        self._url_var = tk.StringVar(value=initial.url if initial else "")
        self._enabled_var = tk.BooleanVar(value=initial.enabled if initial else True)
        self._build()
        self.bind("<Return>", self._on_return)

    def _build(self) -> None:
        ctk.CTkLabel(self, text=ru.GROUP_NAME_LABEL, font=self.fonts.body, anchor="w").pack(
            fill="x", padx=theme.PAD_L, pady=(theme.PAD_L, theme.PAD_XS)
        )
        self._name_entry = ctk.CTkEntry(self, textvariable=self._name_var, width=440)
        self._name_entry.pack(fill="x", padx=theme.PAD_L)

        ctk.CTkLabel(self, text=ru.GROUP_URL_LABEL, font=self.fonts.body, anchor="w").pack(
            fill="x", padx=theme.PAD_L, pady=(theme.PAD_M, theme.PAD_XS)
        )
        self._url_entry = ctk.CTkEntry(self, textvariable=self._url_var, width=440)
        self._url_entry.pack(fill="x", padx=theme.PAD_L)

        self._enabled_box = ctk.CTkCheckBox(
            self, text=ru.GROUP_ENABLED_LABEL, variable=self._enabled_var, font=self.fonts.body
        )
        self._enabled_box.pack(fill="x", padx=theme.PAD_L, pady=theme.PAD_M)

        self._error = ctk.CTkLabel(
            self, text="", font=self.fonts.small, text_color=theme.colour("error"), anchor="w"
        )
        self._error.pack(fill="x", padx=theme.PAD_L)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=theme.PAD_L, pady=theme.PAD_L)
        self._save_button = ctk.CTkButton(buttons, text=ru.ACTION_SAVE, command=self._submit)
        self._save_button.pack(side="left")
        ctk.CTkButton(
            buttons,
            text=ru.ACTION_CANCEL,
            command=self.close,
            **theme.secondary_button(),
        ).pack(side="left", padx=theme.PAD_S)

        self.after(50, self._name_entry.focus_set)

    def _on_return(self, _event: object) -> None:
        self._submit()

    def _submit(self) -> None:
        result = validate_group_form(
            self._name_var.get(), self._url_var.get(), bool(self._enabled_var.get())
        )
        if result.values is None:
            self._error.configure(text=ru.text_for(result.error or ru.ERR_VALIDATION))
            return
        self._error.configure(text="")
        self.set_busy(True)
        self._on_submit(result.values)

    def set_busy(self, busy: bool) -> None:
        """Disable only this dialog's controls while a write is in flight."""
        state = "disabled" if busy else "normal"
        self._name_entry.configure(state=state)
        self._url_entry.configure(state=state)
        self._enabled_box.configure(state=state)
        self._save_button.configure(state=state)

    def show_error(self, text_key: str) -> None:
        """Show a Russian error at the top of the form and re-enable editing."""
        self.set_busy(False)
        self._error.configure(text=ru.text_for(text_key))
