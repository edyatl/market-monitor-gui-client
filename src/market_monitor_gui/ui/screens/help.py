"""Help screen: a read-only operator guide.

Static content only: no services, no network, no task-runner refresh. The body is a
scrolling column of heading/body label pairs. All text comes from
:mod:`market_monitor_gui.texts.ru` via :func:`market_monitor_gui.ui.help_view.help_sections`.
"""

from __future__ import annotations

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.help_view import help_sections
from market_monitor_gui.ui.screens.base import ScreenFrame
from market_monitor_gui.ui.scroll import enable_wheel_scroll

_BODY_WRAP_LENGTH: int = 600


class HelpScreen(ScreenFrame):
    """A scrollable, read-only guide for operators."""

    def __init__(self, master: ctk.CTkFrame, *, fonts: theme.Fonts) -> None:
        super().__init__(master, title=ru.SIDEBAR_HELP, fonts=fonts)

        self._scroll = ctk.CTkScrollableFrame(
            self.body,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=theme.colour("muted"),
        )
        self._scroll.pack(fill="both", expand=True)
        self._scroll.grid_columnconfigure(0, weight=1)
        enable_wheel_scroll(self._scroll)

        for index, section in enumerate(help_sections()):
            ctk.CTkLabel(
                self._scroll,
                text=section.heading,
                font=fonts.section,
                anchor="w",
            ).grid(row=index * 2, column=0, sticky="ew", pady=(theme.PAD_M, theme.PAD_XS))
            ctk.CTkLabel(
                self._scroll,
                text=section.body,
                font=fonts.body,
                text_color=theme.colour("text"),
                justify="left",
                anchor="w",
                wraplength=_BODY_WRAP_LENGTH,
            ).grid(row=index * 2 + 1, column=0, sticky="ew", pady=(0, theme.PAD_S))
