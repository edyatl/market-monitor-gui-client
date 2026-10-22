"""Headless tests for the Help content model (no display required)."""

from __future__ import annotations

import pytest

from market_monitor_gui.texts import ru
from market_monitor_gui.ui.help_view import HelpSection, help_sections
from market_monitor_gui.ui.navigation import SCREEN_LABELS, SCREEN_ORDER

pytestmark = pytest.mark.unit


def test_help_sections_non_empty() -> None:
    sections = help_sections()
    assert sections
    assert all(isinstance(section, HelpSection) for section in sections)


def test_help_sections_have_heading_and_body() -> None:
    for section in help_sections():
        assert section.heading == section.heading.strip()
        assert section.body == section.body.strip()
        assert section.heading
        assert section.body


def test_help_sections_follow_the_expected_order() -> None:
    assert help_sections() == (
        HelpSection(ru.HELP_INTRO_HEADING, ru.HELP_INTRO_BODY),
        HelpSection(ru.HELP_LOGIN_HEADING, ru.HELP_LOGIN_BODY),
        HelpSection(ru.HELP_SECRET_HEADING, ru.HELP_SECRET_BODY),
        HelpSection(ru.HELP_OVERVIEW_HEADING, ru.HELP_OVERVIEW_BODY),
        HelpSection(ru.HELP_GROUPS_HEADING, ru.HELP_GROUPS_BODY),
        HelpSection(ru.HELP_THRESHOLD_HEADING, ru.HELP_THRESHOLD_BODY),
        HelpSection(ru.HELP_FILTERS_HEADING, ru.HELP_FILTERS_BODY),
        HelpSection(ru.HELP_OFFLINE_HEADING, ru.HELP_OFFLINE_BODY),
        HelpSection(
            ru.HELP_KEYS_HEADING,
            "\n".join(
                [
                    *(
                        ru.fmt_help_key(index, SCREEN_LABELS[screen])
                        for index, screen in enumerate(SCREEN_ORDER, start=1)
                    ),
                    ru.HELP_KEYS_REFRESH,
                    ru.HELP_KEYS_ESCAPE,
                ]
            ),
        ),
        HelpSection(ru.HELP_SUPPORT_HEADING, ru.HELP_SUPPORT_BODY),
    )


def test_help_keys_section_matches_the_real_shortcuts() -> None:
    keys = next(section for section in help_sections() if section.heading == ru.HELP_KEYS_HEADING)
    for index, screen in enumerate(SCREEN_ORDER, start=1):
        assert ru.fmt_help_key(index, SCREEN_LABELS[screen]) in keys.body
    assert ru.HELP_KEYS_REFRESH in keys.body
    assert ru.HELP_KEYS_ESCAPE in keys.body


def test_help_headings_are_unique() -> None:
    headings = [section.heading for section in help_sections()]
    assert len(headings) == len(set(headings))
