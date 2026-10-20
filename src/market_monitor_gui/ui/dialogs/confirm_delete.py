"""Destructive confirmation dialog with an optional alternative action.

The destructive button is never the default focus and Enter does not confirm delete
(the dialog binds no Return handler), satisfying the skill's delete-safety rule. A
``409`` from the API can reveal a secondary "disable instead" action without closing
the dialog; at that point the delete is permanently disabled and the alternative is
promoted to the single primary action.
"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.controls import set_button_enabled
from market_monitor_gui.ui.dialogs.base import BaseDialog


class ConfirmDeleteDialog(BaseDialog):
    """Ask the operator to confirm a destructive action naming the item."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        fonts: theme.Fonts,
        question: str,
        confirm_label: str,
        on_confirm: Callable[[], None],
        title: str = ru.CONFIRM_DELETE_TITLE,
    ) -> None:
        super().__init__(master, title=title, fonts=fonts)
        self._on_confirm = on_confirm
        self._alternative: ctk.CTkButton | None = None
        self._conflict = False
        self._build(question, confirm_label)

    def _build(self, question: str, confirm_label: str) -> None:
        ctk.CTkLabel(
            self,
            text=question,
            font=self.fonts.body,
            wraplength=420,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.CONTENT_GUTTER, theme.FIELD_GAP))
        ctk.CTkLabel(
            self,
            text=ru.CONFIRM_DELETE_WARNING,
            font=self.fonts.small,
            text_color=theme.colour("muted"),
            wraplength=420,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.CONTENT_GUTTER)

        self._error = ctk.CTkLabel(
            self,
            text="",
            font=self.fonts.small,
            text_color=theme.colour("error"),
            wraplength=420,
            justify="left",
            anchor="w",
        )
        self._error.pack(fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.BANNER_BOTTOM, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=theme.CONTENT_GUTTER, pady=theme.CONTENT_GUTTER)

        self._cancel_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_CANCEL,
            command=self.close,
            **theme.secondary_button(),
        )
        self._cancel_button.pack(side="left")
        self._confirm_button = ctk.CTkButton(
            buttons,
            text=confirm_label,
            command=self._confirm,
            **theme.destructive_button(),
        )
        self._confirm_button.pack(side="left", padx=theme.TOOLBAR_GAP)

        # Default focus on Cancel so Enter/space never deletes by accident.
        self.after(50, self._cancel_button.focus_set)

    def _confirm(self) -> None:
        self.set_busy(True)
        self._on_confirm()

    def set_busy(self, busy: bool) -> None:
        if self._conflict:
            return
        set_button_enabled(self._confirm_button, not busy, theme.destructive_button())

    def show_error(self, text_key: str) -> None:
        self.set_busy(False)
        self._error.configure(text=ru.text_for(text_key))

    def show_conflict(
        self, text_key: str, action_label: str, on_action: Callable[[], None]
    ) -> None:
        """Show the conflict message and offer the safe alternative.

        The delete is disabled for good (no retry of the same delete) and the
        alternative becomes the single primary action; focus stays on Cancel.
        """
        self._conflict = True
        self._error.configure(text=ru.text_for(text_key))
        set_button_enabled(self._confirm_button, False, theme.destructive_button())
        if self._alternative is None:
            self._alternative = ctk.CTkButton(
                self._confirm_button.master,
                text=action_label,
                command=on_action,
                **theme.primary_button(),
            )
            self._alternative.pack(side="left", before=self._confirm_button, padx=theme.TOOLBAR_GAP)
        self.after(50, self._cancel_button.focus_set)
