"""G15: the shared screen banner and its kind policy."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from market_monitor_gui.ui.banner import Banner, BannerKind

pytestmark = pytest.mark.unit


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _kind(banner: Banner) -> BannerKind | None:
    return banner.kind


def _text(banner: Banner) -> str:
    return banner.text


def _has_action(banner: Banner) -> bool:
    return banner.action is not None


def test_every_kind_has_a_style() -> None:
    from market_monitor_gui.ui.banner import BANNER_STYLES, BannerKind

    assert set(BANNER_STYLES) == set(BannerKind)


def test_only_error_banners_may_carry_an_action() -> None:
    from market_monitor_gui.ui.banner import BannerKind, banner_action_allowed

    allowed = {kind for kind in BannerKind if banner_action_allowed(kind)}
    assert allowed == {BannerKind.ERROR}


def test_banner_glyphs_are_decorative_and_colours_are_palette_tokens() -> None:
    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.banner import BANNER_STYLES

    for style in BANNER_STYLES.values():
        assert style.glyph != ""
        assert not any(ch.isalpha() for ch in style.glyph)
        theme.colour(style.colour)
        theme.colour(style.surface)

    glyphs = {
        ru.BANNER_GLYPH_LOADING,
        ru.BANNER_GLYPH_CACHED,
        ru.BANNER_GLYPH_ERROR,
        ru.BANNER_GLYPH_INFO,
    }
    assert len(glyphs) == 4


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_banner_shows_clears_and_removes_its_empty_strip() -> None:
    import customtkinter as ctk

    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.banner import Banner, BannerKind

    root = ctk.CTk()
    try:
        banner = Banner(root, fonts=theme.build_fonts())
        banner.pack(fill="x")
        root.update()

        banner.show(BannerKind.LOADING, "loading")
        root.update()
        assert _kind(banner) is BannerKind.LOADING
        assert _text(banner) == "loading"
        assert not _has_action(banner)

        banner.show(BannerKind.ERROR, "error", on_action=lambda: None)
        root.update()
        assert _has_action(banner)

        # An error without a callback must not show the retry button.
        banner.show(BannerKind.ERROR, "error")
        root.update()
        assert not _has_action(banner)

        banner.clear()
        root.update()
        assert _kind(banner) is None
        assert _text(banner) == ""
        assert not banner.winfo_manager()
    finally:
        root.destroy()
