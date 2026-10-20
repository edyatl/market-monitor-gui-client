"""Overview screen: read-only dashboard cards with loading/error/cached states.

Rendering only: the shell fetches data through the task runner and hands this screen
an :class:`OverviewData`. Card values are formatted by
:mod:`market_monitor_gui.ui.overview_view` (Tk-free, headless-testable).
"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.services.overview import OverviewData
from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.banner import Banner, BannerKind
from market_monitor_gui.ui.overview_view import overview_cards, scan_run_line
from market_monitor_gui.ui.screens.base import ScreenFrame


class OverviewScreen(ScreenFrame):
    """Shows the main aggregates refreshed through the shell's task runner."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        on_refresh: Callable[[], None],
        on_check: Callable[[], None],
    ) -> None:
        super().__init__(master, title=ru.SIDEBAR_OVERVIEW, fonts=fonts)
        self._on_refresh = on_refresh

        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.pack(fill="x")
        self._refresh_button = ctk.CTkButton(
            toolbar,
            text=ru.ACTION_REFRESH,
            command=on_refresh,
            **theme.primary_button(),
        )
        self._refresh_button.pack(side="left")
        ctk.CTkButton(
            toolbar,
            text=ru.MENU_CHECK_CONNECTION,
            command=on_check,
            **theme.secondary_button(),
        ).pack(side="left", padx=theme.TOOLBAR_GAP)

        self._cards = ctk.CTkFrame(self.body, fg_color="transparent")
        self._banner = Banner(self.body, fonts=fonts, wraplength=640, before=self._cards)
        self._cards.pack(fill="both", expand=True)
        self._cards.grid_columnconfigure(0, weight=1)
        self._cards.grid_columnconfigure(1, weight=1)

        self._scan_line = ctk.CTkLabel(
            self.body,
            text="",
            font=fonts.small,
            text_color=theme.colour("muted"),
            anchor="w",
        )
        self._scan_line.pack(fill="x", pady=(theme.PAD_S, 0))

        self.show_empty_hint()

    # -- state ----------------------------------------------------------------

    def set_busy(self, busy: bool) -> None:
        self._refresh_button.configure(state="disabled" if busy else "normal")

    def set_loading(self) -> None:
        self._banner.show(BannerKind.LOADING, ru.OVERVIEW_LOADING)
        self.set_busy(True)

    def show_empty_hint(self) -> None:
        self._banner.show(BannerKind.INFO, ru.OVERVIEW_EMPTY_HINT)

    def render(self, data: OverviewData) -> None:
        """Render the fetched data, labelling cached/stale values with a time."""
        self._render_cards(data)
        if data.from_cache:
            self._banner.show(BannerKind.CACHED, ru.fmt_data_cached(data.cached_at))
        else:
            self._banner.clear()
        line = scan_run_line(data)
        self._scan_line.configure(text=line or "")
        self.set_busy(False)

    def show_read_error(self, text_key: str) -> None:
        self._banner.show(BannerKind.ERROR, ru.text_for(text_key), on_action=self._on_refresh)
        self.set_busy(False)

    # -- internals ------------------------------------------------------------

    def _render_cards(self, data: OverviewData) -> None:
        for child in self._cards.winfo_children():
            child.destroy()
        for index, card in enumerate(overview_cards(data)):
            frame = ctk.CTkFrame(self._cards)
            frame.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=theme.CARD_GAP,
                pady=theme.CARD_GAP,
            )
            ctk.CTkLabel(
                frame,
                text=card.title,
                font=self._fonts.small,
                text_color=theme.colour("muted"),
                anchor="w",
            ).pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_S, 0))
            ctk.CTkLabel(
                frame,
                text=card.value,
                font=self._fonts.body,
                anchor="w",
                justify="left",
                wraplength=280,
            ).pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_S))
