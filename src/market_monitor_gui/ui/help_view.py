"""Tk-free content model for the Help screen.

Keeps the section order and structure out of the widgets so it can be unit-tested
headless. Every word comes from :mod:`market_monitor_gui.texts.ru`; this module only
pairs a heading with its body.
"""

from __future__ import annotations

from dataclasses import dataclass

from market_monitor_gui.texts import ru
from market_monitor_gui.ui.navigation import SCREEN_LABELS, SCREEN_ORDER


@dataclass(frozen=True, slots=True)
class HelpSection:
    """One read-only section of the operator guide."""

    heading: str
    body: str


def _keys_body() -> str:
    """List the implemented shortcuts, deriving Ctrl+1..5 from the navigation order."""
    lines = [
        ru.fmt_help_key(index, SCREEN_LABELS[screen])
        for index, screen in enumerate(SCREEN_ORDER, start=1)
    ]
    lines.append(ru.HELP_KEYS_REFRESH)
    lines.append(ru.HELP_KEYS_ESCAPE)
    return "\n".join(lines)


def help_sections() -> tuple[HelpSection, ...]:
    """Return the operator guide sections in display order."""
    return (
        HelpSection(ru.HELP_INTRO_HEADING, ru.HELP_INTRO_BODY),
        HelpSection(ru.HELP_LOGIN_HEADING, ru.HELP_LOGIN_BODY),
        HelpSection(ru.HELP_OVERVIEW_HEADING, ru.HELP_OVERVIEW_BODY),
        HelpSection(ru.HELP_GROUPS_HEADING, ru.HELP_GROUPS_BODY),
        HelpSection(ru.HELP_THRESHOLD_HEADING, ru.HELP_THRESHOLD_BODY),
        HelpSection(ru.HELP_FILTERS_HEADING, ru.HELP_FILTERS_BODY),
        HelpSection(ru.HELP_OFFLINE_HEADING, ru.HELP_OFFLINE_BODY),
        HelpSection(ru.HELP_KEYS_HEADING, _keys_body()),
        HelpSection(ru.HELP_SUPPORT_HEADING, ru.HELP_SUPPORT_BODY),
    )
