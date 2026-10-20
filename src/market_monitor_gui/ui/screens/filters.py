"""Filters screen: list exclusion phrases with add and delete actions.

Rendering plus callbacks only: the shell fetches and mutates through services on the
task runner. Filters are add/delete only — the contract exposes no filter update, so
``enabled`` is shown read-only. All operator text comes from
:mod:`market_monitor_gui.texts.ru`.
"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.api.dto import FilterResponse
from market_monitor_gui.services.filters import FiltersData
from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.banner import Banner, BannerKind
from market_monitor_gui.ui.controls import button_state, set_button_enabled
from market_monitor_gui.ui.filters_view import filter_state_text, normalized_line, sort_filters
from market_monitor_gui.ui.screens.base import ScreenFrame
from market_monitor_gui.ui.scroll import enable_wheel_scroll


class FiltersScreen(ScreenFrame):
    """A vertical list of exclusion rows with a toolbar and status banner."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        on_refresh: Callable[[], None],
        on_add: Callable[[], None],
        on_delete: Callable[[FilterResponse], None],
    ) -> None:
        super().__init__(master, title=ru.SIDEBAR_FILTERS, fonts=fonts)
        self._on_delete = on_delete
        self._on_refresh = on_refresh
        self._rows: dict[int, _FilterRow] = {}
        self._loading = False
        self._read_only = False

        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.pack(fill="x")
        self._toolbar = toolbar
        self._add_button = ctk.CTkButton(
            toolbar,
            text=ru.ACTION_ADD,
            command=on_add,
            **theme.primary_button(),
        )
        self._add_button.pack(side="left")
        self._refresh_button = ctk.CTkButton(
            toolbar,
            text=ru.ACTION_REFRESH,
            command=on_refresh,
            **theme.secondary_button(),
        )
        self._refresh_button.pack(side="left", padx=theme.TOOLBAR_GAP)

        self._count = ctk.CTkLabel(
            toolbar, text="", font=fonts.small, text_color=theme.colour("muted"), anchor="e"
        )
        self._count.pack(side="right", padx=(theme.TOOLBAR_GAP, 0))

        self._list = ctk.CTkScrollableFrame(
            self.body,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=theme.colour("muted"),
        )
        self._banner = Banner(self.body, fonts=fonts, wraplength=720, after=self._toolbar)
        self._list.pack(fill="both", expand=True)
        self._list.grid_columnconfigure(0, weight=1)
        enable_wheel_scroll(self._list)

        self._empty = ctk.CTkLabel(
            self._list,
            text=ru.FILTERS_EMPTY,
            font=fonts.body,
            text_color=theme.colour("muted"),
            anchor="w",
        )

    # -- state ----------------------------------------------------------------

    def set_loading(self) -> None:
        self._loading = True
        self._banner.show(BannerKind.LOADING, ru.FILTERS_LOADING)
        self._apply_state()

    def render(self, data: FiltersData) -> None:
        """Rebuild the rows from server data (sorted by phrase)."""
        for row in self._rows.values():
            row.destroy()
        self._rows.clear()

        self._read_only = data.from_cache
        filters = sort_filters(data.filters)
        self._empty.pack_forget()
        for index, item in enumerate(filters):
            row = _FilterRow(
                self._list,
                fonts=self._fonts,
                item=item,
                on_delete=self._on_delete,
            )
            row.set_read_only(self._read_only)
            row.grid(row=index, column=0, sticky="ew", pady=theme.ROW_PAD_Y)
            self._rows[item.id] = row

        self._count.configure(text=ru.fmt_filters_count(len(filters)))
        if not filters:
            self._empty.grid(row=0, column=0, sticky="w", pady=theme.ROW_PAD_Y)
        if data.from_cache:
            self._banner.show(BannerKind.CACHED, ru.fmt_data_cached_readonly(data.cached_at))
        else:
            self._banner.clear()
        self._loading = False
        self._apply_state()

    def show_read_error(self, text_key: str) -> None:
        """The read failed: report it and lock mutations until a successful read."""
        self._read_only = True
        self._loading = False
        self._banner.show(
            BannerKind.ERROR,
            ru.fmt_readonly_notice(ru.text_for(text_key)),
            on_action=self._on_refresh,
        )
        self._apply_state()

    def show_write_error(self, text_key: str) -> None:
        """A mutation failed: report it but keep the controls usable for a retry."""
        self._loading = False
        self._banner.show(BannerKind.ERROR, ru.text_for(text_key))
        self._apply_state()

    def _apply_state(self) -> None:
        set_button_enabled(self._refresh_button, not self._loading, theme.secondary_button())
        set_button_enabled(
            self._add_button,
            not (self._loading or self._read_only),
            theme.primary_button(),
        )
        for row in self._rows.values():
            row.set_read_only(self._read_only)

    def set_row_busy(self, filter_id: int, busy: bool) -> None:
        row = self._rows.get(filter_id)
        if row is not None:
            row.set_busy(busy)

    # -- callbacks ------------------------------------------------------------

    def on_show(self) -> None:
        """Rows are refreshed by the shell when the screen is shown."""


class _FilterRow(ctk.CTkFrame):
    """One exclusion row: phrase, normalized form, state, and a delete action."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        item: FilterResponse,
        on_delete: Callable[[FilterResponse], None],
    ) -> None:
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self._busy = False
        self._read_only = False

        ctk.CTkLabel(self, text=item.phrase, font=fonts.body, anchor="w").grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(theme.ROW_PAD_X, 0),
            pady=(theme.ROW_PAD_Y, 0),
        )
        self._normalized = ctk.CTkLabel(
            self,
            text=normalized_line(item),
            font=fonts.small,
            text_color=theme.colour("muted"),
            anchor="w",
        )
        self._normalized.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(theme.ROW_PAD_X, 0),
            pady=(0, theme.ROW_PAD_Y),
        )
        if not self._normalized.cget("text"):
            self._normalized.grid_remove()

        ctk.CTkLabel(self, text=filter_state_text(item.enabled), font=fonts.small, anchor="e").grid(
            row=0, column=1, rowspan=2, padx=theme.ROW_ACTION_INSET
        )

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, sticky="e", padx=theme.ROW_ACTION_INSET)
        self._delete = ctk.CTkButton(
            actions,
            text=ru.ACTION_DELETE,
            width=theme.BUTTON_WIDTH_NARROW,
            font=fonts.small,
            command=lambda: on_delete(item),
            **theme.destructive_button(),
        )
        self._delete.pack(side="left", padx=theme.ROW_ACTION_GAP)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._apply_state()

    def set_read_only(self, read_only: bool) -> None:
        self._read_only = read_only
        self._apply_state()

    def _apply_state(self) -> None:
        enabled = button_state(busy=self._busy, read_only=self._read_only) == "normal"
        set_button_enabled(self._delete, enabled, theme.destructive_button())
