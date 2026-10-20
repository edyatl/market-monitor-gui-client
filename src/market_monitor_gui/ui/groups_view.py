"""Tk-free formatting helpers for the Groups screen.

Keeps sorting/labels/truncation out of the widgets so they can be unit-tested
headless. Strings come from :mod:`market_monitor_gui.texts.ru` only.
"""

from __future__ import annotations

from collections.abc import Iterable

from market_monitor_gui.api.dto import GroupResponse
from market_monitor_gui.texts import ru


def sort_groups(groups: Iterable[GroupResponse]) -> list[GroupResponse]:
    """Return groups ordered by name (case-insensitive), stable by id."""
    return sorted(groups, key=lambda group: (group.name.casefold(), group.id))


def group_state_text(enabled: bool) -> str:
    """Text (with glyph) for a group's enabled state; never colour alone."""
    return ru.GROUP_STATE_ENABLED if enabled else ru.GROUP_STATE_DISABLED


def toggle_action_text(enabled: bool) -> str:
    """Label for the enable/disable row action."""
    return ru.ACTION_DISABLE if enabled else ru.ACTION_ENABLE


def ellipsize(text: str, limit: int) -> str:
    """Truncate ``text`` to ``limit`` characters, appending an ellipsis when cut."""
    if limit <= 1 or len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def ellipsize_middle(text: str, limit: int) -> str:
    """Truncate ``text`` in the middle, keeping both the head and the tail.

    Used for URLs, where the scheme (head) and the identifying tail matter more than
    the middle. The result never exceeds ``limit`` characters.
    """
    if limit <= 1 or len(text) <= limit:
        return text
    keep = limit - 1
    head = (keep + 1) // 2
    tail = keep - head
    return text[:head] + "…" + (text[-tail:] if tail else "")
