"""G9: Tk-free Groups presentation helpers."""

from __future__ import annotations

import pytest

from market_monitor_gui.api.dto import GroupResponse
from market_monitor_gui.texts import ru
from market_monitor_gui.ui.groups_view import (
    ellipsize,
    ellipsize_middle,
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


def test_ellipsize_middle_keeps_head_and_tail() -> None:
    url = "https://shop.example/catalog/very/long/path/to/a/product/123456"
    result = ellipsize_middle(url, 48)
    assert len(result) == 48
    assert result.startswith("https://shop.example")
    assert result.endswith(url[-1])
    assert "…" in result


def test_ellipsize_middle_leaves_short_text_untouched() -> None:
    assert ellipsize_middle("https://shop.example/1", 72) == "https://shop.example/1"


def test_ellipsize_middle_handles_tiny_limits() -> None:
    assert ellipsize_middle("abcdef", 1) == "abcdef"
    assert ellipsize_middle("abcdef", 2) == "a…"
