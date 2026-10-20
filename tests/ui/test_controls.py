"""G14: one place decides whether a role-styled control is enabled and how it looks."""

from __future__ import annotations

from typing import Any

import pytest

from market_monitor_gui.ui import theme
from market_monitor_gui.ui.controls import button_state, set_button_enabled

pytestmark = pytest.mark.unit


class _FakeButton:
    """Records ``configure`` calls so the helper can be tested without a display."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def configure(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


@pytest.mark.parametrize(
    ("busy", "read_only", "expected"),
    [
        (False, False, "normal"),
        (True, False, "disabled"),
        (False, True, "disabled"),
        (True, True, "disabled"),
    ],
)
def test_button_state_truth_table(busy: bool, read_only: bool, expected: str) -> None:
    assert button_state(busy=busy, read_only=read_only) == expected


def test_enabled_button_gets_its_role_back() -> None:
    button = _FakeButton()
    set_button_enabled(button, True, theme.primary_button())

    assert button.calls == [{**theme.primary_button(), "state": "normal"}]


def test_disabled_button_gets_the_muted_look() -> None:
    button = _FakeButton()
    set_button_enabled(button, False, theme.destructive_button())

    assert button.calls == [{**theme.disabled_button(), "state": "disabled"}]
    assert button.calls[0]["fg_color"] != theme.destructive_button()["fg_color"]


def test_re_enabling_restores_the_original_role() -> None:
    button = _FakeButton()
    role = theme.secondary_button()
    set_button_enabled(button, False, role)
    set_button_enabled(button, True, role)

    assert button.calls[-1] == {**role, "state": "normal"}
