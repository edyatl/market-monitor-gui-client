"""Placeholder screen for sections implemented in a later batch."""

from __future__ import annotations

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.screens.base import ScreenFrame


class PlaceholderScreen(ScreenFrame):
    """A short "coming soon" panel."""

    def __init__(self, master: ctk.CTkFrame, *, title: str, fonts: theme.Fonts) -> None:
        super().__init__(master, title=title, fonts=fonts)
        ctk.CTkLabel(self.body, text=ru.SCREEN_STUB_TITLE, font=fonts.section, anchor="w").pack(
            fill="x", pady=(0, theme.PAD_S)
        )
        ctk.CTkLabel(
            self.body,
            text=ru.SCREEN_STUB_HINT,
            font=fonts.body,
            text_color=theme.colour("muted"),
            wraplength=640,
            justify="left",
            anchor="w",
        ).pack(fill="x")
