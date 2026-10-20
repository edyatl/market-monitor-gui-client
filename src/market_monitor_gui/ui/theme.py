"""Fonts, spacing, and the semantic colour palette for the GUI.

Screens import the constants here instead of hardcoding sizes or hex colours. Fonts
are built lazily by :func:`build_fonts` because ``CTkFont`` requires a Tk root; the
module stays importable without a display.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

import customtkinter as ctk

# -- spacing (8 px base) ------------------------------------------------------

PAD_XS: Final[int] = 4
PAD_S: Final[int] = 8
PAD_M: Final[int] = 16
PAD_L: Final[int] = 24

# -- region tokens (one padding per screen region) ----------------------------

CONTENT_GUTTER: Final[int] = PAD_L
TITLE_TOP: Final[int] = PAD_L
TITLE_BOTTOM: Final[int] = PAD_M
TOOLBAR_GAP: Final[int] = PAD_S
BANNER_TOP: Final[int] = PAD_XS
BANNER_BOTTOM: Final[int] = PAD_S
SECTION_GAP: Final[int] = PAD_M
FIELD_GAP: Final[int] = PAD_XS
FIELD_BOTTOM: Final[int] = PAD_XS
CARD_GAP: Final[int] = PAD_XS

# -- row density (list rows) --------------------------------------------------

ROW_PAD_X: Final[int] = PAD_S
ROW_PAD_Y: Final[int] = PAD_XS
ROW_CELL_GAP: Final[int] = PAD_XS
ROW_ACTION_GAP: Final[int] = PAD_XS
ROW_ACTION_INSET: Final[int] = PAD_S

# -- button metrics -----------------------------------------------------------

BUTTON_WIDTH_NARROW: Final[int] = 90
BUTTON_WIDTH_MEDIUM: Final[int] = 110

SIDEBAR_WIDTH: Final[int] = 200
MIN_WIDTH: Final[int] = 900
MIN_HEIGHT: Final[int] = 600
STATUS_BAR_HEIGHT: Final[int] = 32

# -- typography ---------------------------------------------------------------

FONT_TITLE_SIZE: Final[int] = 20
FONT_SECTION_SIZE: Final[int] = 15
FONT_BODY_SIZE: Final[int] = 13
FONT_SMALL_SIZE: Final[int] = 11

# -- appearance ---------------------------------------------------------------

DEFAULT_APPEARANCE: Final[str] = "system"
APPEARANCE_MODES: Final[tuple[str, ...]] = ("system", "light", "dark")

#: Semantic colours as ``(light, dark)`` tuples. Never use raw hex in screens.
PALETTE: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "ok": ("#1a7f37", "#3fb950"),
        "warn": ("#9a6700", "#d29922"),
        "error": ("#cf222e", "#f85149"),
        "error_hover": ("#b91c1c", "#da3633"),
        "muted": ("#57606a", "#8b949e"),
        "accent": ("#0969da", "#2f81f7"),
        "accent_hover": ("#0a5cbf", "#2569c9"),
        "text": ("#1a1a1a", "#dce4ee"),
        "on_accent": ("#ffffff", "#ffffff"),
        "hover": ("#e3e8ee", "#343a40"),
        "surface": ("#f6f7f9", "#2b2f36"),
        "disabled_surface": ("#e6e8eb", "#2f333a"),
    }
)


def colour(name: str) -> tuple[str, str]:
    """Return the ``(light, dark)`` tuple for a semantic colour name."""
    return PALETTE[name]


def primary_button() -> dict[str, object]:
    """Keyword args for the single filled accent action of a view or dialog."""
    return {
        "fg_color": colour("accent"),
        "hover_color": colour("accent_hover"),
        "text_color": colour("on_accent"),
    }


def secondary_button() -> dict[str, object]:
    """Keyword args for a low-emphasis (ghost) button.

    Uses a transparent fill with explicit text/hover colours so labels stay readable on
    the light default background (the raw CustomTkinter default is a light grey that is
    unreadable on white). Primary actions keep their filled accent styling.
    """
    return {
        "fg_color": "transparent",
        "text_color": colour("text"),
        "hover_color": colour("hover"),
    }


def destructive_button() -> dict[str, object]:
    """Keyword args for a red-toned button used only for destructive actions."""
    return {
        "fg_color": colour("error"),
        "hover_color": colour("error_hover"),
        "text_color": colour("on_accent"),
    }


def link_button() -> dict[str, object]:
    """Keyword args for an inline link-styled button (opens an external URL)."""
    return {
        "fg_color": "transparent",
        "hover_color": colour("hover"),
        "text_color": colour("accent"),
        "corner_radius": 0,
    }


def nav_active_button() -> dict[str, object]:
    """Keyword args for the currently selected sidebar item."""
    return {
        "fg_color": colour("accent"),
        "hover_color": colour("accent_hover"),
        "text_color": colour("on_accent"),
    }


def nav_inactive_button() -> dict[str, object]:
    """Keyword args for an unselected sidebar item."""
    return secondary_button()


def disabled_button() -> dict[str, object]:
    """Keyword args for the inactive look of any role-styled button.

    CustomTkinter keeps a disabled button's fill and only dims the label, which leaves
    an accent-filled button looking enabled and a muted label unreadable on that fill.
    Swapping to a muted surface makes the inactive state unambiguous.
    """
    return {
        "fg_color": colour("disabled_surface"),
        "hover_color": colour("disabled_surface"),
        "text_color": colour("muted"),
        "text_color_disabled": colour("muted"),
    }


def apply_appearance(mode: str) -> str:
    """Apply ``mode`` (``system``/``light``/``dark``); fall back to the default."""
    selected = mode if mode in APPEARANCE_MODES else DEFAULT_APPEARANCE
    ctk.set_appearance_mode(selected)
    return selected


@dataclass(frozen=True, slots=True)
class Fonts:
    """Named fonts shared by the shell, screens, and dialogs."""

    title: ctk.CTkFont
    section: ctk.CTkFont
    body: ctk.CTkFont
    small: ctk.CTkFont
    link: ctk.CTkFont


def build_fonts() -> Fonts:
    """Create the font set. Must be called after a Tk root exists."""
    return Fonts(
        title=ctk.CTkFont(size=FONT_TITLE_SIZE, weight="bold"),
        section=ctk.CTkFont(size=FONT_SECTION_SIZE, weight="bold"),
        body=ctk.CTkFont(size=FONT_BODY_SIZE),
        small=ctk.CTkFont(size=FONT_SMALL_SIZE),
        link=ctk.CTkFont(size=FONT_BODY_SIZE, underline=True),
    )
