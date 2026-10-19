"""Screen identifiers and their sidebar labels (labels come from ``texts/ru.py``)."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from market_monitor_gui.texts import ru


class Screen(StrEnum):
    """The five top-level screens. Values double as UI-state keys."""

    OVERVIEW = "overview"
    GROUPS = "groups"
    SETTINGS = "settings"
    FILTERS = "filters"
    HELP = "help"


SCREEN_ORDER: tuple[Screen, ...] = (
    Screen.OVERVIEW,
    Screen.GROUPS,
    Screen.FILTERS,
    Screen.SETTINGS,
    Screen.HELP,
)

SCREEN_LABELS: Mapping[Screen, str] = {
    Screen.OVERVIEW: ru.SIDEBAR_OVERVIEW,
    Screen.GROUPS: ru.SIDEBAR_GROUPS,
    Screen.SETTINGS: ru.SIDEBAR_SETTINGS,
    Screen.FILTERS: ru.SIDEBAR_FILTERS,
    Screen.HELP: ru.SIDEBAR_HELP,
}


def screen_from_value(value: str | None) -> Screen:
    """Return the stored screen, defaulting to Overview for unknown values."""
    if value is None:
        return Screen.OVERVIEW
    try:
        return Screen(value)
    except ValueError:
        return Screen.OVERVIEW
