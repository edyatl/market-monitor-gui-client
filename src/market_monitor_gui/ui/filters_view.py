"""Tk-free formatting helpers for the Filters (exclusions) screen.

Keeps sorting/labels out of the widgets so they can be unit-tested headless. Strings
come from :mod:`market_monitor_gui.texts.ru` only.
"""

from __future__ import annotations

from collections.abc import Iterable

from market_monitor_gui.api.dto import FilterResponse
from market_monitor_gui.texts import ru


def sort_filters(filters: Iterable[FilterResponse]) -> list[FilterResponse]:
    """Return filters ordered by phrase (case-insensitive), stable by id."""
    return sorted(filters, key=lambda item: (item.phrase.casefold(), item.id))


def filter_state_text(enabled: bool) -> str:
    """Text (with glyph) for a filter's enabled state; never colour alone."""
    return ru.FILTER_STATE_ENABLED if enabled else ru.FILTER_STATE_DISABLED


def normalized_line(item: FilterResponse) -> str:
    """The normalized-phrase note, or an empty string when the server sends none."""
    if not item.normalized_phrase:
        return ""
    return ru.fmt_filter_normalized(item.normalized_phrase)
