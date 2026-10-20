"""G14: semantic role helpers and density tokens stay centralised in the theme."""

from __future__ import annotations

import pytest

from market_monitor_gui.ui import theme

pytestmark = pytest.mark.unit

_ROLE_HELPERS = (
    theme.primary_button,
    theme.secondary_button,
    theme.destructive_button,
    theme.link_button,
    theme.nav_active_button,
    theme.nav_inactive_button,
    theme.disabled_button,
)

_DENSITY_TOKENS = (
    theme.CONTENT_GUTTER,
    theme.TITLE_TOP,
    theme.TITLE_BOTTOM,
    theme.TOOLBAR_GAP,
    theme.BANNER_TOP,
    theme.BANNER_BOTTOM,
    theme.SECTION_GAP,
    theme.FIELD_GAP,
    theme.FIELD_BOTTOM,
    theme.CARD_GAP,
    theme.ROW_PAD_X,
    theme.ROW_PAD_Y,
    theme.ROW_CELL_GAP,
    theme.ROW_ACTION_GAP,
    theme.ROW_ACTION_INSET,
    theme.BUTTON_WIDTH_NARROW,
    theme.BUTTON_WIDTH_MEDIUM,
)


def test_palette_entries_are_light_dark_pairs() -> None:
    for name, value in theme.PALETTE.items():
        assert len(value) == 2, f"{name} must have a light and a dark colour"
        assert all(isinstance(colour, str) and colour.startswith("#") for colour in value)


def test_role_helpers_return_style_keywords() -> None:
    for helper in _ROLE_HELPERS:
        kwargs = helper()
        assert kwargs, f"{helper.__name__} must return styling keywords"
        assert all(isinstance(key, str) for key in kwargs)


def test_primary_uses_the_app_accent() -> None:
    kwargs = theme.primary_button()
    assert kwargs["fg_color"] == theme.colour("accent")
    assert kwargs["hover_color"] == theme.colour("accent_hover")
    assert kwargs["text_color"] == theme.colour("on_accent")


def test_destructive_uses_the_error_palette_with_its_own_hover() -> None:
    kwargs = theme.destructive_button()
    assert kwargs["fg_color"] == theme.colour("error")
    assert kwargs["hover_color"] == theme.colour("error_hover")
    assert kwargs["hover_color"] != kwargs["fg_color"]


def test_secondary_and_nav_inactive_are_ghost_buttons() -> None:
    for kwargs in (theme.secondary_button(), theme.nav_inactive_button()):
        assert kwargs["fg_color"] == "transparent"
        assert kwargs["text_color"] == theme.colour("text")


def test_nav_active_uses_the_accent() -> None:
    kwargs = theme.nav_active_button()
    assert kwargs["fg_color"] == theme.colour("accent")
    assert kwargs["text_color"] == theme.colour("on_accent")


def test_link_is_flat_and_accent_coloured() -> None:
    kwargs = theme.link_button()
    assert kwargs["fg_color"] == "transparent"
    assert kwargs["text_color"] == theme.colour("accent")
    assert kwargs["corner_radius"] == 0


def test_disabled_look_is_muted_in_both_appearance_modes() -> None:
    kwargs = theme.disabled_button()
    assert kwargs["fg_color"] == theme.colour("disabled_surface")
    assert kwargs["hover_color"] == theme.colour("disabled_surface")
    assert kwargs["text_color"] == theme.colour("muted")
    assert kwargs["text_color_disabled"] == theme.colour("muted")


def test_density_tokens_are_positive_sizes() -> None:
    for token in _DENSITY_TOKENS:
        assert isinstance(token, int)
        assert token > 0
