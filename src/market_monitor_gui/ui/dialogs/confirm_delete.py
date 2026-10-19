"""Destructive confirmation dialog with an optional alternative action.

The destructive button is never the default focus and Enter does not confirm delete
(the dialog binds no Return handler), satisfying the skill's delete-safety rule. A
``409`` from the API can reveal a secondary "disable instead" action without closing
the dialog.
"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
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
    ) -> None:
        super().__init__(master, title=ru.CONFIRM_DELETE_TITLE, fonts=fonts)
        self._on_confirm = on_confirm
        self._alternative: ctk.CTkButton | None = None
        self._build(question, confirm_label)

    def _build(self, question: str, confirm_label: str) -> None:
        ctk.CTkLabel(
            self,
            text=question,
            font=self.fonts.body,
            wraplength=420,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_L, theme.PAD_XS))
        ctk.CTkLabel(
            self,
            text=ru.CONFIRM_DELETE_WARNING,
            font=self.fonts.small,
            text_color=theme.colour("muted"),
            wraplength=420,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=theme.PAD_L)

        self._error = ctk.CTkLabel(
            self,
            text="",
            font=self.fonts.small,
            text_color=theme.colour("error"),
            wraplength=420,
            justify="left",
            anchor="w",
        )
        self._error.pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_S, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=theme.PAD_L, pady=theme.PAD_L)

        self._cancel_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_CANCEL,
            fg_color="transparent",
            hover_color=theme.colour("muted"),
            command=self.close,
        )
        self._cancel_button.pack(side="left")
        self._confirm_button = ctk.CTkButton(
            buttons,
            text=confirm_label,
            fg_color=theme.colour("error"),
            hover_color=theme.colour("error"),
            command=self._confirm,
        )
        self._confirm_button.pack(side="left", padx=theme.PAD_S)

        # Default focus on Cancel so Enter/space never deletes by accident.
        self.after(50, self._cancel_button.focus_set)

    def _confirm(self) -> None:
        self.set_busy(True)
        self._on_confirm()

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self._confirm_button.configure(state=state)
        if self._alternative is not None:
            self._alternative.configure(state=state)

    def show_error(self, text_key: str) -> None:
        self.set_busy(False)
        self._error.configure(text=ru.text_for(text_key))

    def reveal_alternative(
        self, text_key: str, action_label: str, on_action: Callable[[], None]
    ) -> None:
        """Show the conflict message and a secondary action button (e.g. disable)."""
        self.set_busy(False)
        self._error.configure(text=ru.text_for(text_key))
        if self._alternative is None:
            self._alternative = ctk.CTkButton(
                self._confirm_button.master,
                text=action_label,
                fg_color="transparent",
                hover_color=theme.colour("muted"),
                command=on_action,
            )
            self._alternative.pack(side="right")
