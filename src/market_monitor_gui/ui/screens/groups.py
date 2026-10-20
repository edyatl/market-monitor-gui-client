"""Groups screen: list groups with add/edit/enable-disable/delete actions.

Rendering plus callbacks only: the shell fetches and mutates through services on the
task runner. Each row owns its controls so a single in-flight mutation disables only
that row. All operator text comes from :mod:`market_monitor_gui.texts.ru`.
"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.api.dto import GroupResponse
from market_monitor_gui.services.groups import GroupsData
from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.banner import Banner, BannerKind
from market_monitor_gui.ui.controls import button_state, set_button_enabled
from market_monitor_gui.ui.groups_view import (
    ellipsize,
    group_state_text,
    sort_groups,
    toggle_action_text,
)
from market_monitor_gui.ui.screens.base import ScreenFrame
from market_monitor_gui.ui.scroll import enable_wheel_scroll

_URL_DISPLAY_LIMIT = 72


class GroupsScreen(ScreenFrame):
    """A vertical list of group rows with a toolbar and status banner."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        on_refresh: Callable[[], None],
        on_add: Callable[[], None],
        on_edit: Callable[[GroupResponse], None],
        on_toggle: Callable[[GroupResponse], None],
        on_delete: Callable[[GroupResponse], None],
        on_open_url: Callable[[str], None],
    ) -> None:
        super().__init__(master, title=ru.SIDEBAR_GROUPS, fonts=fonts)
        self._on_edit = on_edit
        self._on_toggle = on_toggle
        self._on_delete = on_delete
        self._on_refresh = on_refresh
        self._on_open_url = on_open_url
        self._rows: dict[int, _GroupRow] = {}
        self._busy: set[int] = set()
        self._loading = False
        self._read_only = False

        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.pack(fill="x")
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
            self.body, text="", font=fonts.small, text_color=theme.colour("muted"), anchor="w"
        )
        self._count.pack(fill="x", pady=(theme.BANNER_TOP, 0))

        self._list = ctk.CTkScrollableFrame(
            self.body,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=theme.colour("muted"),
        )
        self._banner = Banner(self.body, fonts=fonts, wraplength=720, after=self._count)
        self._list.pack(fill="both", expand=True)
        self._list.grid_columnconfigure(0, weight=1)
        enable_wheel_scroll(self._list)

        self._empty = ctk.CTkLabel(
            self._list,
            text=ru.GROUPS_EMPTY,
            font=fonts.body,
            text_color=theme.colour("muted"),
            anchor="w",
        )

    # -- state ----------------------------------------------------------------

    def set_loading(self) -> None:
        self._loading = True
        self._banner.show(BannerKind.LOADING, ru.GROUPS_LOADING)
        self._apply_state()

    def render(self, data: GroupsData) -> None:
        """Rebuild the rows from server data (sorted by name)."""
        for row in self._rows.values():
            row.destroy()
        self._rows.clear()
        self._busy.clear()

        self._read_only = data.from_cache
        groups = sort_groups(data.groups)
        self._empty.pack_forget()
        for index, group in enumerate(groups):
            row = _GroupRow(
                self._list,
                fonts=self._fonts,
                group=group,
                on_edit=self._on_edit,
                on_toggle=self._on_toggle,
                on_delete=self._on_delete,
                on_open_url=self._on_open_url,
            )
            row.set_read_only(self._read_only)
            row.grid(row=index, column=0, sticky="ew", pady=theme.ROW_PAD_Y)
            self._rows[group.id] = row

        self._count.configure(text=ru.fmt_groups_count(len(groups)))
        if not groups:
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

    def set_row_busy(self, group_id: int, busy: bool) -> None:
        row = self._rows.get(group_id)
        if row is None:
            return
        if busy:
            self._busy.add(group_id)
        else:
            self._busy.discard(group_id)
        row.set_busy(busy)

    def show_conflict(self, group_id: int) -> None:
        """Show the 409 guidance on a row; its toggle offers the disable action."""
        row = self._rows.get(group_id)
        if row is not None:
            row.show_conflict()

    # -- callbacks ------------------------------------------------------------

    def on_show(self) -> None:
        """Rows are refreshed by the shell when the screen is shown."""


class _GroupRow(ctk.CTkFrame):
    """One group row: name/url, enabled state, and inline row actions."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        group: GroupResponse,
        on_edit: Callable[[GroupResponse], None],
        on_toggle: Callable[[GroupResponse], None],
        on_delete: Callable[[GroupResponse], None],
        on_open_url: Callable[[str], None],
    ) -> None:
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self._busy = False
        self._read_only = False

        ctk.CTkLabel(self, text=group.name, font=fonts.body, anchor="w").grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(theme.ROW_PAD_X, 0),
            pady=(theme.ROW_PAD_Y, 0),
        )
        self._open_url = ctk.CTkButton(
            self,
            text=ellipsize(group.url, _URL_DISPLAY_LIMIT),
            font=fonts.link,
            anchor="w",
            command=lambda: on_open_url(group.url),
            **theme.link_button(),
        )
        self._open_url.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(theme.ROW_PAD_X, 0),
            pady=(0, theme.ROW_PAD_Y),
        )

        ctk.CTkLabel(self, text=group_state_text(group.enabled), font=fonts.small, anchor="e").grid(
            row=0, column=1, rowspan=2, padx=theme.ROW_ACTION_INSET
        )

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, sticky="e", padx=theme.ROW_ACTION_INSET)
        self._edit = ctk.CTkButton(
            actions,
            text=ru.ACTION_EDIT,
            width=theme.BUTTON_WIDTH_NARROW,
            font=fonts.small,
            command=lambda: on_edit(group),
            **theme.secondary_button(),
        )
        self._edit.pack(side="left", padx=theme.ROW_ACTION_GAP)
        self._toggle = ctk.CTkButton(
            actions,
            text=toggle_action_text(group.enabled),
            width=theme.BUTTON_WIDTH_MEDIUM,
            font=fonts.small,
            command=lambda: on_toggle(group),
            **theme.secondary_button(),
        )
        self._toggle.pack(side="left", padx=theme.ROW_ACTION_GAP)
        self._delete = ctk.CTkButton(
            actions,
            text=ru.ACTION_DELETE,
            width=theme.BUTTON_WIDTH_NARROW,
            font=fonts.small,
            command=lambda: on_delete(group),
            **theme.destructive_button(),
        )
        self._delete.pack(side="left", padx=theme.ROW_ACTION_GAP)

        self._hint = ctk.CTkLabel(
            self,
            text="",
            font=fonts.small,
            text_color=theme.colour("error"),
            anchor="w",
            justify="left",
            wraplength=720,
        )
        self._hint.grid(row=2, column=0, columnspan=3, sticky="ew", padx=theme.ROW_PAD_X)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._apply_state()

    def set_read_only(self, read_only: bool) -> None:
        self._read_only = read_only
        self._apply_state()

    def _apply_state(self) -> None:
        enabled = button_state(busy=self._busy, read_only=self._read_only) == "normal"
        set_button_enabled(self._edit, enabled, theme.secondary_button())
        set_button_enabled(self._toggle, enabled, theme.secondary_button())
        set_button_enabled(self._delete, enabled, theme.destructive_button())

    def show_conflict(self) -> None:
        self._hint.configure(text=ru.ERR_CONFLICT_GROUP_IN_USE)
