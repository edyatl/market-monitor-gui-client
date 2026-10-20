"""Base class for screens shown in the content area."""

from __future__ import annotations

import customtkinter as ctk

from market_monitor_gui.ui import theme


class ScreenFrame(ctk.CTkFrame):
    """A titled content frame with a body container and show/hide hooks."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        title: str,
        fonts: theme.Fonts,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._fonts = fonts
        ctk.CTkLabel(self, text=title, font=fonts.title, anchor="w").pack(
            fill="x",
            padx=theme.CONTENT_GUTTER,
            pady=(theme.TITLE_TOP, theme.TITLE_BOTTOM),
        )
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(
            fill="both",
            expand=True,
            padx=theme.CONTENT_GUTTER,
            pady=(0, theme.CONTENT_GUTTER),
        )

    def on_show(self) -> None:
        """Called when the screen becomes visible."""

    def on_hide(self) -> None:
        """Called when the screen is replaced."""
