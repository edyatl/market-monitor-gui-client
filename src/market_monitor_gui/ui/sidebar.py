"""Fixed left sidebar: navigation buttons and a footer for the application menu."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.controls import set_button_enabled
from market_monitor_gui.ui.navigation import SCREEN_ORDER, Screen, screen_button_text


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
        self._enabled = True

        title = ctk.CTkLabel(self, text=ru.APP_NAME, font=fonts.section, anchor="w")
        title.pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_M, theme.PAD_S))

        for screen in SCREEN_ORDER:
            button = ctk.CTkButton(
                self,
                text=screen_button_text(screen),
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
        self._apply_states()

    def clear_active(self) -> None:
        """De-highlight every item (used on the unauthenticated screen)."""
        self._active = None
        self._apply_states()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self._apply_states()

    def _role_for(self, screen: Screen) -> dict[str, object]:
        if screen is self._active:
            return theme.nav_active_button()
        return theme.nav_inactive_button()

    def _apply_states(self) -> None:
        for screen, button in self._buttons.items():
            set_button_enabled(button, self._enabled, self._role_for(screen))
            font = self._fonts.section if screen is self._active else self._fonts.body
            button.configure(font=font)
