"""Fixed left sidebar: navigation buttons and a footer for the application menu."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.navigation import SCREEN_LABELS, SCREEN_ORDER, Screen


class Sidebar(ctk.CTkFrame):
    """Navigation column. Selection is highlighted with fill and bold text."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        fonts: theme.Fonts,
        on_select: Callable[[Screen], None],
    ) -> None:
        super().__init__(master, width=theme.SIDEBAR_WIDTH, corner_radius=0)
        self.grid_propagate(False)
        self._fonts = fonts
        self._on_select = on_select
        self._buttons: dict[Screen, ctk.CTkButton] = {}
        self._active: Screen | None = None

        title = ctk.CTkLabel(self, text=ru.APP_NAME, font=fonts.section, anchor="w")
        title.pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_M, theme.PAD_S))

        for screen in SCREEN_ORDER:
            button = ctk.CTkButton(
                self,
                text=SCREEN_LABELS[screen],
                anchor="w",
                font=fonts.body,
                **theme.secondary_button(),
                command=lambda selected=screen: self._on_select(selected),
            )
            button.pack(fill="x", padx=theme.PAD_S, pady=theme.PAD_XS)
            self._buttons[screen] = button

    def footer(self) -> ctk.CTkFrame:
        """Container for the application-menu button, pinned to the bottom."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(side="bottom", fill="x", padx=theme.PAD_S, pady=theme.PAD_M)
        return frame

    def set_active(self, screen: Screen) -> None:
        self._active = screen
        for candidate, button in self._buttons.items():
            if candidate is screen:
                button.configure(
                    fg_color=theme.colour("accent"),
                    hover_color=theme.colour("accent_hover"),
                    text_color=theme.colour("on_accent"),
                    font=self._fonts.section,
                )
            else:
                button.configure(
                    fg_color="transparent",
                    hover_color=theme.colour("hover"),
                    text_color=theme.colour("text"),
                    font=self._fonts.body,
                )

    def clear_active(self) -> None:
        """De-highlight every item (used on the unauthenticated screen)."""
        self._active = None
        for button in self._buttons.values():
            button.configure(
                fg_color="transparent",
                hover_color=theme.colour("hover"),
                text_color=theme.colour("text"),
                font=self._fonts.body,
            )

    def set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for button in self._buttons.values():
            button.configure(state=state)
