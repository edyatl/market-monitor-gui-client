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
            fill="x", padx=theme.PAD_L, pady=(theme.PAD_L, theme.PAD_XS)
        )
        ctk.CTkLabel(self, text=ru.fmt_version(__version__), font=self.fonts.body, anchor="w").pack(
            fill="x", padx=theme.PAD_L, pady=(0, theme.PAD_L)
        )

        ctk.CTkButton(self, text=ru.ACTION_CLOSE, command=self.close).pack(
            anchor="e", padx=theme.PAD_L, pady=(0, theme.PAD_L)
        )
