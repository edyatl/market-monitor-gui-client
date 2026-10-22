"""G1: the Russian text registry."""

from __future__ import annotations

import re

import pytest

from market_monitor_gui.texts import ru

pytestmark = pytest.mark.unit

_CYRILLIC = re.compile(r"[\u0400-\u04ff]")


def test_text_for_returns_registered_value() -> None:
    assert ru.text_for("ACTION_RETRY") == ru.ACTION_RETRY


def test_text_for_unknown_key_raises_keyerror_naming_the_key() -> None:
    with pytest.raises(KeyError) as excinfo:
        ru.text_for("DOES_NOT_EXIST")
    assert "DOES_NOT_EXIST" in str(excinfo.value)


def test_registry_excludes_meta_constants() -> None:
    assert "TEXT_KEYS" not in ru.TEXT_KEYS
    assert "EMPTY_PLACEHOLDERS" not in ru.TEXT_KEYS


def test_placeholders_are_registered_and_empty() -> None:
    assert ru.EMPTY_PLACEHOLDERS  # non-empty set
    for key in ru.EMPTY_PLACEHOLDERS:
        assert key in ru.TEXT_KEYS, f"placeholder {key} is not a registered text key"
        assert ru.TEXT_KEYS[key] == "", f"placeholder {key} must stay empty for now"


def test_every_error_constant_is_registered_and_russian() -> None:
    error_keys = [name for name in ru.TEXT_KEYS if name.startswith("ERR_")]
    assert error_keys, "no ERR_* text keys registered"
    for name in error_keys:
        assert _CYRILLIC.search(ru.TEXT_KEYS[name]), f"{name} must contain Russian text"


def test_required_error_keys_exist() -> None:
    required = {
        "ERR_NETWORK",
        "ERR_TIMEOUT",
        "ERR_UNAUTHORIZED",
        "ERR_SESSION_EXPIRED",
        "ERR_FORBIDDEN",
        "ERR_NOT_FOUND",
        "ERR_VALIDATION",
        "ERR_CONFLICT",
        "ERR_CONFLICT_GROUP_IN_USE",
        "ERR_RATE_LIMIT",
        "ERR_SERVER",
        "ERR_BAD_RESPONSE",
        "ERR_NO_SECRET",
        "ERR_SECRET_REQUIRED",
        "ERR_OPEN_LINK",
    }
    assert required <= set(ru.TEXT_KEYS)


def test_status_strings_carry_text_not_only_a_glyph() -> None:
    status_keys = [name for name in ru.TEXT_KEYS if name.startswith("STATUS_")]
    assert status_keys
    for name in status_keys:
        assert _CYRILLIC.search(ru.TEXT_KEYS[name]), f"{name} must include words"


def test_menu_and_sidebar_labels_exist() -> None:
    required = {
        "SIDEBAR_OVERVIEW",
        "SIDEBAR_GROUPS",
        "SIDEBAR_SETTINGS",
        "SIDEBAR_FILTERS",
        "SIDEBAR_HELP",
        "MENU_CONNECTION_SETTINGS",
        "MENU_CHECK_CONNECTION",
        "MENU_DISCONNECT",
        "MENU_ABOUT",
    }
    assert required <= set(ru.TEXT_KEYS)


def test_navigation_icon_keys_exist_and_are_glyphs() -> None:
    required = {
        "SIDEBAR_ICON_OVERVIEW",
        "SIDEBAR_ICON_GROUPS",
        "SIDEBAR_ICON_FILTERS",
        "SIDEBAR_ICON_SETTINGS",
        "SIDEBAR_ICON_HELP",
        "MENU_ICON",
    }
    assert required <= set(ru.TEXT_KEYS)
    for name in required:
        value = ru.TEXT_KEYS[name]
        assert value != ""
        assert not _CYRILLIC.search(value), f"{name} must be a decorative glyph, not words"


def test_feedback_glyph_keys_exist_and_are_decorative() -> None:
    required = {
        "BANNER_GLYPH_LOADING",
        "BANNER_GLYPH_CACHED",
        "BANNER_GLYPH_ERROR",
        "BANNER_GLYPH_INFO",
        "MSG_GLYPH_INFO",
        "MSG_GLYPH_SUCCESS",
        "MSG_GLYPH_WARN",
        "MSG_GLYPH_ERROR",
    }
    assert required <= set(ru.TEXT_KEYS)
    for name in required:
        value = ru.TEXT_KEYS[name]
        assert value != ""
        assert not _CYRILLIC.search(value), f"{name} must be a decorative glyph, not words"


def test_group_disabled_is_russian() -> None:
    assert _CYRILLIC.search(ru.GROUP_DISABLED)


def test_settings_keys_exist() -> None:
    required = {
        "LABEL_THRESHOLD",
        "SETTINGS_THRESHOLD_HINT",
        "SETTINGS_PERCENT_SUFFIX",
        "SETTINGS_THRESHOLD_REQUIRED",
        "SETTINGS_THRESHOLD_NOT_A_NUMBER",
        "SETTINGS_THRESHOLD_OUT_OF_RANGE",
        "SETTINGS_LOADING",
        "SETTINGS_SAVED",
    }
    assert required <= set(ru.TEXT_KEYS)


def test_settings_hint_states_the_enforced_range() -> None:
    from market_monitor_gui.ui.forms import THRESHOLD_MAX, THRESHOLD_MIN
    from market_monitor_gui.ui.settings_view import format_threshold

    assert format_threshold(THRESHOLD_MIN) in ru.SETTINGS_THRESHOLD_HINT
    assert format_threshold(THRESHOLD_MAX) in ru.SETTINGS_THRESHOLD_HINT


def test_threshold_copy_mentions_the_usual_default_and_server_value() -> None:
    assert "5 %" in ru.SETTINGS_THRESHOLD_HINT
    assert "5 %" in ru.HELP_THRESHOLD_BODY
    assert "по умолчанию" in ru.SETTINGS_THRESHOLD_HINT.lower()
    assert "сервер" in ru.SETTINGS_THRESHOLD_HINT.lower()
    assert "сервер" in ru.HELP_THRESHOLD_BODY.lower()


def test_filters_keys_exist() -> None:
    required = {
        "FILTERS_LOADING",
        "FILTERS_EMPTY",
        "FILTERS_COUNT",
        "FILTERS_SAVED",
        "FILTERS_DELETED",
        "FILTER_EDITOR_TITLE_ADD",
        "FILTER_PHRASE_LABEL",
        "FILTER_PHRASE_HINT",
        "FILTER_PHRASE_REQUIRED",
        "FILTER_PHRASE_TOO_LONG",
        "FILTER_NORMALIZED_VALUE",
        "FILTER_STATE_ENABLED",
        "FILTER_STATE_DISABLED",
        "CONFIRM_DELETE_FILTER_TITLE",
    }
    assert required <= set(ru.TEXT_KEYS)


def test_filter_copy_states_the_all_words_rule() -> None:
    for text in (ru.HELP_FILTERS_BODY, ru.FILTER_PHRASE_HINT):
        lowered = text.lower()
        assert "все её слова" in lowered
        assert "регистр" in lowered
        assert "порядок" in lowered


def test_readonly_keys_exist_and_are_russian() -> None:
    required = {"DATA_CACHED_READONLY", "READONLY_NOTICE"}
    assert required <= set(ru.TEXT_KEYS)
    for name in required:
        assert _CYRILLIC.search(ru.TEXT_KEYS[name]), f"{name} must contain Russian text"


def test_cached_readonly_note_keeps_the_help_prefix() -> None:
    from datetime import UTC, datetime

    when = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    text = ru.fmt_data_cached_readonly(None)
    assert text.startswith(ru.fmt_data_cached(None))
    assert ru.fmt_data_cached_readonly(when) != ru.fmt_data_cached(when)


def test_readonly_notice_appends_the_consequence() -> None:
    reason = ru.ERR_NETWORK
    assert ru.fmt_readonly_notice(reason) == f"{reason} {ru.READONLY_NOTICE}"
    assert ru.fmt_readonly_notice("") == ru.READONLY_NOTICE


def test_help_offline_body_still_quotes_the_cached_prefix() -> None:
    prefix = ru.DATA_CACHED.split("{when}")[0].strip()
    assert prefix in ru.HELP_OFFLINE_BODY


def test_help_keys_exist() -> None:
    required = {
        "HELP_INTRO_HEADING",
        "HELP_INTRO_BODY",
        "HELP_LOGIN_HEADING",
        "HELP_LOGIN_BODY",
        "HELP_OVERVIEW_HEADING",
        "HELP_OVERVIEW_BODY",
        "HELP_GROUPS_HEADING",
        "HELP_GROUPS_BODY",
        "HELP_THRESHOLD_HEADING",
        "HELP_THRESHOLD_BODY",
        "HELP_FILTERS_HEADING",
        "HELP_FILTERS_BODY",
        "HELP_OFFLINE_HEADING",
        "HELP_OFFLINE_BODY",
        "HELP_KEYS_HEADING",
        "HELP_KEYS_ITEM",
        "HELP_KEYS_REFRESH",
        "HELP_KEYS_ESCAPE",
        "HELP_SUPPORT_HEADING",
        "HELP_SUPPORT_BODY",
    }
    assert required <= set(ru.TEXT_KEYS)


def test_help_offline_body_mentions_the_retry_action() -> None:
    assert ru.ACTION_RETRY in ru.HELP_OFFLINE_BODY
