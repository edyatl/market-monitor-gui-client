"""About dialog: application name and version."""

from __future__ import annotations

import customtkinter as ctk

from market_monitor_gui import __version__
from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.dialogs.base import BaseDialog


class AboutDialog(BaseDialog):
    """Read-only name/version dialog."""

    def __init__(self, master: ctk.CTk, *, fonts: theme.Fonts) -> None:
        super().__init__(master, title=ru.ABOUT_TITLE, fonts=fonts)

        ctk.CTkLabel(self, text=ru.APP_NAME, font=self.fonts.title, anchor="w").pack(
            fill="x", padx=theme.CONTENT_GUTTER, pady=(theme.CONTENT_GUTTER, theme.FIELD_GAP)
        )
        ctk.CTkLabel(self, text=ru.fmt_version(__version__), font=self.fonts.body, anchor="w").pack(
            fill="x", padx=theme.CONTENT_GUTTER, pady=(0, theme.CONTENT_GUTTER)
        )

        ctk.CTkButton(
            self,
            text=ru.ACTION_CLOSE,
            command=self.close,
            **theme.secondary_button(),
        ).pack(anchor="e", padx=theme.CONTENT_GUTTER, pady=(0, theme.CONTENT_GUTTER))
