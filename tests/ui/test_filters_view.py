"""G11: Tk-free Filters (exclusions) presentation helpers."""

from __future__ import annotations

import pytest

from market_monitor_gui.api.dto import FilterResponse
from market_monitor_gui.texts import ru
from market_monitor_gui.ui.filters_view import filter_state_text, normalized_line, sort_filters

pytestmark = pytest.mark.unit


def _filter(filter_id: int, phrase: str, normalized: str = "") -> FilterResponse:
    return FilterResponse(
        id=filter_id,
        phrase=phrase,
        normalized_phrase=normalized,
        enabled=True,
        created_at="2026-10-18T10:00:00+00:00",
        updated_at="2026-10-18T10:00:00+00:00",
    )


def test_sort_filters_is_case_insensitive_by_phrase() -> None:
    filters = [_filter(2, "бета"), _filter(1, "Альфа"), _filter(3, "гамма")]
    assert [item.phrase for item in sort_filters(filters)] == ["Альфа", "бета", "гамма"]


def test_filter_state_text_carries_words_and_glyph() -> None:
    assert filter_state_text(True) == ru.FILTER_STATE_ENABLED
    assert filter_state_text(False) == ru.FILTER_STATE_DISABLED


def test_normalized_line_is_formatted_when_present() -> None:
    item = _filter(1, "no spam", "no spam")
    assert normalized_line(item) == ru.fmt_filter_normalized("no spam")


def test_normalized_line_is_empty_when_absent() -> None:
    assert normalized_line(_filter(1, "no spam", "")) == ""
