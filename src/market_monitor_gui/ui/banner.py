"""Shared inline feedback banner for screens (loading / cached / error / info).

One widget replaces the per-screen banner labels. Screens pass already-formatted
strings from :mod:`market_monitor_gui.texts.ru`; the widget holds no Russian literals
(glyphs are named constants in ``ru.py``). An empty banner removes itself from the
layout entirely, so no blank strip is left behind.

Only the ``error`` kind may carry an action button (the retry action); the button
uses a theme role and is enabled/disabled through :func:`ui.controls.set_button_enabled`.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.controls import set_button_enabled


class BannerKind(StrEnum):
    """Semantic kinds of screen-level feedback."""

    LOADING = "loading"
    CACHED = "cached"
    ERROR = "error"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class BannerStyle:
    """Presentation for one banner kind: glyph, text colour, and background."""

    glyph: str
    colour: str
    surface: str


BANNER_STYLES: Final[Mapping[BannerKind, BannerStyle]] = MappingProxyType(
    {
        BannerKind.LOADING: BannerStyle(ru.BANNER_GLYPH_LOADING, "muted", "surface"),
        BannerKind.CACHED: BannerStyle(ru.BANNER_GLYPH_CACHED, "warn", "warn_surface"),
        BannerKind.ERROR: BannerStyle(ru.BANNER_GLYPH_ERROR, "error", "error_surface"),
        BannerKind.INFO: BannerStyle(ru.BANNER_GLYPH_INFO, "info_text", "info_surface"),
    }
)


def banner_action_allowed(kind: BannerKind) -> bool:
    """Return whether a banner of ``kind`` may carry an action button."""
    return kind is BannerKind.ERROR


class Banner(ctk.CTkFrame):
    """One inline feedback strip: glyph + message, optional error action."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        wraplength: int = 720,
        pady: tuple[int, int] = (theme.BANNER_TOP, theme.BANNER_BOTTOM),
        before: tk.Misc | None = None,
        after: tk.Misc | None = None,
    ) -> None:
        super().__init__(master, fg_color=theme.colour("surface"), corner_radius=0)
        self._kind: BannerKind | None = None
        self._text = ""
        self._pady = pady
        self._before = before
        self._after = after
        self._on_action: Callable[[], None] | None = None
        self._action_label = ru.ACTION_RETRY

        self._action: ctk.CTkButton = ctk.CTkButton(
            self,
            text=ru.ACTION_RETRY,
            font=fonts.small,
            command=self._invoke_action,
            **theme.secondary_button(),
        )

        self._label = ctk.CTkLabel(
            self,
            text="",
            font=fonts.small,
            anchor="w",
            justify="left",
            wraplength=wraplength,
        )
        self._label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(theme.PAD_S, theme.PAD_XS),
            pady=theme.PAD_XS,
        )

    # -- read API -------------------------------------------------------------

    @property
    def kind(self) -> BannerKind | None:
        """The kind currently shown, or ``None`` when hidden."""
        return self._kind

    @property
    def text(self) -> str:
        """The message currently shown, without the glyph prefix."""
        return self._text

    @property
    def display_text(self) -> str:
        """The rendered label text (glyph + message)."""
        return str(self._label.cget("text"))

    @property
    def action(self) -> ctk.CTkButton | None:
        """The action button when it is visible, else ``None``."""
        return self._action if self._action.winfo_manager() else None

    # -- state ----------------------------------------------------------------

    def show(
        self,
        kind: BannerKind,
        text: str,
        *,
        on_action: Callable[[], None] | None = None,
        action_label: str = ru.ACTION_RETRY,
    ) -> None:
        """Show ``text`` for ``kind``; attach the retry action only for errors."""
        style = BANNER_STYLES[kind]
        self._kind = kind
        self._text = text
        self._label.configure(
            text=f"{style.glyph} {text}" if text else "",
            text_color=theme.colour(style.colour),
        )
        self.configure(fg_color=theme.colour(style.surface))
        self._set_action(kind, on_action, action_label)
        self._reveal()

    def clear(self) -> None:
        """Hide the banner and drop it from the layout (no empty strip)."""
        self._kind = None
        self._text = ""
        self._label.configure(text="")
        self._set_action(None, None, ru.ACTION_RETRY)
        self.pack_forget()

    # -- internals ------------------------------------------------------------

    def _reveal(self) -> None:
        if self.winfo_manager():
            return
        if self._before is not None:
            self.pack(fill="x", pady=self._pady, before=self._before)
        elif self._after is not None:
            self.pack(fill="x", pady=self._pady, after=self._after)
        else:
            self.pack(fill="x", pady=self._pady)

    def _set_action(
        self,
        kind: BannerKind | None,
        on_action: Callable[[], None] | None,
        action_label: str,
    ) -> None:
        allowed = kind is not None and banner_action_allowed(kind) and on_action is not None
        self._on_action = on_action if allowed else None
        self._action_label = action_label
        if not allowed:
            self._action.pack_forget()
            return
        self._action.configure(text=action_label)
        set_button_enabled(self._action, True, theme.secondary_button())
        self._action.pack(side="right", padx=(0, theme.PAD_S), pady=theme.PAD_XS)

    def _invoke_action(self) -> None:
        if self._on_action is not None:
            self._on_action()
