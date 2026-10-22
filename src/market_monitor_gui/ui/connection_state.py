"""Connection state shown in the status bar, and its mapping from errors.

Tkinter-free so the mapping can be unit-tested headless and reused by both the shell
and the status bar.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.texts import ru


class ConnectionState(StrEnum):
    """Connection lifecycle shown in the status bar."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    RETRYING = "retrying"
    OFFLINE = "offline"
    DISCONNECTED = "disconnected"
    SESSION_EXPIRED = "session_expired"


STATE_TEXT: Mapping[ConnectionState, str] = {
    ConnectionState.CONNECTING: ru.STATUS_CONNECTING,
    ConnectionState.CONNECTED: ru.STATUS_CONNECTED,
    ConnectionState.RETRYING: ru.STATUS_RETRYING,
    ConnectionState.OFFLINE: ru.STATUS_OFFLINE,
    ConnectionState.DISCONNECTED: ru.STATUS_DISCONNECTED,
    ConnectionState.SESSION_EXPIRED: ru.STATUS_SESSION_EXPIRED,
}


def status_text(state: ConnectionState) -> str:
    """Return the operator-facing text (with glyph) for ``state``."""
    return STATE_TEXT[state]


def state_for_error(exc: BaseException) -> ConnectionState | None:
    """Return the connection state implied by ``exc``, or ``None`` to keep the current."""
    if isinstance(exc, ApiError):
        if exc.kind in (ErrorKind.NETWORK, ErrorKind.TIMEOUT):
            return ConnectionState.OFFLINE
        if exc.kind is ErrorKind.UNAUTHORIZED:
            return ConnectionState.SESSION_EXPIRED
    return None
