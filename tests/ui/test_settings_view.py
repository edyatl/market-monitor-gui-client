"""G10: Tk-free Settings presentation helper."""

from __future__ import annotations

import pytest

from market_monitor_gui.ui.settings_view import format_threshold

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (7.5, "7,5"),
        (25.0, "25"),
        (0.1, "0,1"),
        (100.0, "100"),
        (12.345, "12,345"),
    ],
)
def test_format_threshold_uses_comma_and_drops_trailing_zero(value: float, expected: str) -> None:
    assert format_threshold(value) == expected
