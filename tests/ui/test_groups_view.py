"""G9: Tk-free Groups presentation helpers."""

from __future__ import annotations

import pytest

from market_monitor_gui.api.dto import GroupResponse
from market_monitor_gui.texts import ru
from market_monitor_gui.ui.groups_view import (
    ellipsize,
    group_state_text,
    sort_groups,
    toggle_action_text,
)

pytestmark = pytest.mark.unit


def _group(group_id: int, name: str) -> GroupResponse:
    return GroupResponse(
        id=group_id,
        name=name,
        url=f"https://shop.example/{group_id}",
        enabled=True,
        sort_order=0,
        created_at="2026-10-18T10:00:00+00:00",
        updated_at="2026-10-18T10:00:00+00:00",
    )


def test_sort_groups_is_case_insensitive_by_name() -> None:
    groups = [_group(2, "beta"), _group(1, "Alpha"), _group(3, "gamma")]
    assert [group.name for group in sort_groups(groups)] == ["Alpha", "beta", "gamma"]


def test_group_state_text_carries_words_and_glyph() -> None:
    assert group_state_text(True) == ru.GROUP_STATE_ENABLED
    assert group_state_text(False) == ru.GROUP_STATE_DISABLED


def test_toggle_action_text_reflects_current_state() -> None:
    assert toggle_action_text(True) == ru.ACTION_DISABLE
    assert toggle_action_text(False) == ru.ACTION_ENABLE


def test_ellipsize_truncates_with_ellipsis() -> None:
    assert ellipsize("short", 10) == "short"
    result = ellipsize("a" * 100, 10)
    assert len(result) == 10
    assert result.endswith("…")
