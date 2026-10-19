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
from market_monitor_gui.ui.filters_view import filter_state_text, normalized_line, sort_filters
from market_monitor_gui.ui.screens.base import ScreenFrame


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
        self._rows: dict[int, _FilterRow] = {}

        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.pack(fill="x")
        self._add_button = ctk.CTkButton(toolbar, text=ru.ACTION_ADD, command=on_add)
        self._add_button.pack(side="left")
        self._refresh_button = ctk.CTkButton(
            toolbar,
            text=ru.ACTION_REFRESH,
            command=on_refresh,
            **theme.secondary_button(),
        )
        self._refresh_button.pack(side="left", padx=theme.PAD_S)

        self._count = ctk.CTkLabel(
            self.body, text="", font=fonts.small, text_color=theme.colour("muted"), anchor="w"
        )
        self._count.pack(fill="x", pady=(theme.PAD_S, 0))

        self._banner = ctk.CTkLabel(
            self.body,
            text="",
            font=fonts.small,
            text_color=theme.colour("warn"),
            wraplength=720,
            justify="left",
            anchor="w",
        )
        self._banner.pack(fill="x", pady=(theme.PAD_XS, theme.PAD_S))

        self._list = ctk.CTkScrollableFrame(self.body, fg_color="transparent")
        self._list.pack(fill="both", expand=True)
        self._list.grid_columnconfigure(0, weight=1)

        self._empty = ctk.CTkLabel(
            self._list,
            text=ru.FILTERS_EMPTY,
            font=fonts.body,
            text_color=theme.colour("muted"),
            anchor="w",
        )

    # -- state ----------------------------------------------------------------

    def set_loading(self) -> None:
        self._banner.configure(text=ru.FILTERS_LOADING, text_color=theme.colour("muted"))
        self._refresh_button.configure(state="disabled")
        self._add_button.configure(state="disabled")

    def render(self, data: FiltersData) -> None:
        """Rebuild the rows from server data (sorted by phrase)."""
        for row in self._rows.values():
            row.destroy()
        self._rows.clear()

        filters = sort_filters(data.filters)
        self._empty.pack_forget()
        for index, item in enumerate(filters):
            row = _FilterRow(
                self._list,
                fonts=self._fonts,
                item=item,
                on_delete=self._on_delete,
            )
            row.grid(row=index, column=0, sticky="ew", pady=theme.PAD_XS)
            self._rows[item.id] = row

        self._count.configure(text=ru.fmt_filters_count(len(filters)))
        if not filters:
            self._empty.grid(row=0, column=0, sticky="w", pady=theme.PAD_S)
        if data.from_cache:
            self._banner.configure(
                text=ru.fmt_data_cached(data.cached_at), text_color=theme.colour("warn")
            )
        else:
            self._banner.configure(text="", text_color=theme.colour("warn"))
        self._refresh_button.configure(state="normal")
        self._add_button.configure(state="normal")

    def show_error(self, text_key: str) -> None:
        self._banner.configure(text=ru.text_for(text_key), text_color=theme.colour("error"))
        self._refresh_button.configure(state="normal")
        self._add_button.configure(state="normal")

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

        ctk.CTkLabel(self, text=item.phrase, font=fonts.body, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=(theme.PAD_S, 0), pady=(theme.PAD_XS, 0)
        )
        ctk.CTkLabel(
            self,
            text=normalized_line(item),
            font=fonts.small,
            text_color=theme.colour("muted"),
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=(theme.PAD_S, 0), pady=(0, theme.PAD_XS))

        ctk.CTkLabel(self, text=filter_state_text(item.enabled), font=fonts.small, anchor="e").grid(
            row=0, column=1, rowspan=2, padx=theme.PAD_S
        )

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, sticky="e", padx=theme.PAD_S)
        self._delete = ctk.CTkButton(
            actions,
            text=ru.ACTION_DELETE,
            width=90,
            font=fonts.small,
            fg_color=theme.colour("error"),
            hover_color=theme.colour("error"),
            command=lambda: on_delete(item),
        )
        self._delete.pack(side="left", padx=theme.PAD_XS)

    def set_busy(self, busy: bool) -> None:
        self._delete.configure(state="disabled" if busy else "normal")
