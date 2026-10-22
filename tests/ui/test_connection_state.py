"""Connection-state text and error mapping (Tk-free)."""

from __future__ import annotations

import pytest

from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.texts import ru
from market_monitor_gui.ui.connection_state import (
    ConnectionState,
    state_for_error,
    status_text,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (ConnectionState.CONNECTING, ru.STATUS_CONNECTING),
        (ConnectionState.CONNECTED, ru.STATUS_CONNECTED),
        (ConnectionState.RETRYING, ru.STATUS_RETRYING),
        (ConnectionState.OFFLINE, ru.STATUS_OFFLINE),
        (ConnectionState.DISCONNECTED, ru.STATUS_DISCONNECTED),
        (ConnectionState.SESSION_EXPIRED, ru.STATUS_SESSION_EXPIRED),
    ],
)
def test_status_text_has_glyph_and_text(state: ConnectionState, expected: str) -> None:
    assert status_text(state) == expected
    assert expected.strip() != ""


@pytest.mark.parametrize("kind", [ErrorKind.NETWORK, ErrorKind.TIMEOUT])
def test_network_errors_map_to_offline(kind: ErrorKind) -> None:
    assert state_for_error(ApiError(kind)) is ConnectionState.OFFLINE


def test_unauthorized_maps_to_session_expired() -> None:
    assert state_for_error(ApiError(ErrorKind.UNAUTHORIZED)) is ConnectionState.SESSION_EXPIRED


def test_server_error_keeps_current_state() -> None:
    assert state_for_error(ApiError(ErrorKind.SERVER)) is None
    assert state_for_error(RuntimeError("x")) is None
