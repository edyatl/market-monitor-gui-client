"""Bottom status bar: connection state plus a transient message slot.

State is always shown as text (the ``STATUS_*`` strings already carry a glyph), never
by colour alone. The bar is a plain view: the shell decides the state and calls the
setters. Transient messages carry a :class:`MessageKind` that picks a glyph, a colour,
and a linger time; there is a single slot, so messages never stack.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Final

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.connection_state import ConnectionState, status_text

#: Semantic colour per state. Colour is only ever a supplement: the state text always
#: carries a glyph and words (skill rule "status is never colour-only").
_STATE_COLOUR: Mapping[ConnectionState, str] = {
    ConnectionState.CONNECTING: "muted",
    ConnectionState.CONNECTED: "ok",
    ConnectionState.RETRYING: "warn",
    ConnectionState.OFFLINE: "error",
    ConnectionState.DISCONNECTED: "muted",
    ConnectionState.SESSION_EXPIRED: "warn",
}


class MessageKind(StrEnum):
    """Kind of a transient status-bar message (glyph + colour + linger time)."""

    INFO = "info"
    SUCCESS = "success"
    WARN = "warn"
    ERROR = "error"


#: Glyph and palette colour per message kind.
_MESSAGE_STYLES: Mapping[MessageKind, tuple[str, str]] = MappingProxyType(
    {
        MessageKind.INFO: (ru.MSG_GLYPH_INFO, "accent"),
        MessageKind.SUCCESS: (ru.MSG_GLYPH_SUCCESS, "ok"),
        MessageKind.WARN: (ru.MSG_GLYPH_WARN, "warn"),
        MessageKind.ERROR: (ru.MSG_GLYPH_ERROR, "error"),
    }
)

#: How long a message stays before the shell clears it. Errors linger longest so the
#: operator has time to read them; a new message always replaces the current one.
MESSAGE_TTL_MS: Final[Mapping[MessageKind, int]] = MappingProxyType(
    {
        MessageKind.INFO: 4000,
        MessageKind.SUCCESS: 4000,
        MessageKind.WARN: 7000,
        MessageKind.ERROR: 10000,
    }
)


class StatusBar(ctk.CTkFrame):
    """Left: connection state. Right: transient message and/or last refresh time."""

    def __init__(self, master: ctk.CTkFrame, *, fonts: theme.Fonts) -> None:
        super().__init__(master, height=theme.STATUS_BAR_HEIGHT, corner_radius=0)
        self._last_refresh: datetime | None = None
        self._message: str | None = None
        self._message_kind: MessageKind = MessageKind.INFO

        self._state_label = ctk.CTkLabel(
            self,
            text=status_text(ConnectionState.CONNECTING),
            font=fonts.body,
            text_color=theme.colour(_STATE_COLOUR[ConnectionState.CONNECTING]),
        )
        self._state_label.pack(side="left", padx=theme.PAD_M, pady=theme.PAD_XS)

        self._info_label = ctk.CTkLabel(self, text="", font=fonts.small)
        self._info_label.pack(side="right", padx=theme.PAD_M, pady=theme.PAD_XS)

    def set_state(self, state: ConnectionState) -> None:
        self._state_label.configure(
            text=status_text(state), text_color=theme.colour(_STATE_COLOUR[state])
        )

    def set_message(self, message: str | None, kind: MessageKind = MessageKind.INFO) -> None:
        self._message = message
        self._message_kind = kind
        self._render_info()

    def set_last_refresh(self, when: datetime | None) -> None:
        self._last_refresh = when
        self._render_info()

    def _render_info(self) -> None:
        if self._message:
            glyph, colour = _MESSAGE_STYLES[self._message_kind]
            self._info_label.configure(
                text=f"{glyph} {self._message}", text_color=theme.colour(colour)
            )
        elif self._last_refresh is not None:
            self._info_label.configure(
                text=ru.fmt_last_refresh(self._last_refresh), text_color=theme.colour("muted")
            )
        else:
            self._info_label.configure(text="")
