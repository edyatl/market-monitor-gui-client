"""Bottom status bar: connection state plus a transient message slot.

State is always shown as text (the ``STATUS_*`` strings already carry a glyph), never
by colour alone. The bar is a plain view: the shell decides the state and calls the
setters.
"""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.connection_state import ConnectionState, status_text


class StatusBar(ctk.CTkFrame):
    """Left: connection state. Right: transient message and/or last refresh time."""

    def __init__(self, master: ctk.CTkFrame, *, fonts: theme.Fonts) -> None:
        super().__init__(master, height=theme.STATUS_BAR_HEIGHT, corner_radius=0)
        self._last_refresh: datetime | None = None
        self._message: str | None = None

        self._state_label = ctk.CTkLabel(
            self, text=status_text(ConnectionState.CONNECTING), font=fonts.body
        )
        self._state_label.pack(side="left", padx=theme.PAD_M, pady=theme.PAD_XS)

        self._info_label = ctk.CTkLabel(self, text="", font=fonts.small)
        self._info_label.pack(side="right", padx=theme.PAD_M, pady=theme.PAD_XS)

    def set_state(self, state: ConnectionState) -> None:
        self._state_label.configure(text=status_text(state))

    def set_message(self, message: str | None) -> None:
        self._message = message
        self._render_info()

    def set_last_refresh(self, when: datetime | None) -> None:
        self._last_refresh = when
        self._render_info()

    def _render_info(self) -> None:
        if self._message:
            self._info_label.configure(text=self._message)
        elif self._last_refresh is not None:
            self._info_label.configure(text=ru.fmt_last_refresh(self._last_refresh))
        else:
            self._info_label.configure(text="")
