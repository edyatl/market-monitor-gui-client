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
from market_monitor_gui.ui.groups_view import (
    ellipsize,
    group_state_text,
    sort_groups,
    toggle_action_text,
)
from market_monitor_gui.ui.screens.base import ScreenFrame

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
    ) -> None:
        super().__init__(master, title=ru.SIDEBAR_GROUPS, fonts=fonts)
        self._on_edit = on_edit
        self._on_toggle = on_toggle
        self._on_delete = on_delete
        self._rows: dict[int, _GroupRow] = {}
        self._busy: set[int] = set()

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
            text=ru.GROUPS_EMPTY,
            font=fonts.body,
            text_color=theme.colour("muted"),
            anchor="w",
        )

    # -- state ----------------------------------------------------------------

    def set_loading(self) -> None:
        self._banner.configure(text=ru.GROUPS_LOADING, text_color=theme.colour("muted"))
        self._refresh_button.configure(state="disabled")

    def render(self, data: GroupsData) -> None:
        """Rebuild the rows from server data (sorted by name)."""
        for row in self._rows.values():
            row.destroy()
        self._rows.clear()
        self._busy.clear()

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
            )
            row.grid(row=index, column=0, sticky="ew", pady=theme.PAD_XS)
            self._rows[group.id] = row

        self._count.configure(text=ru.fmt_groups_count(len(groups)))
        if not groups:
            self._empty.grid(row=0, column=0, sticky="w", pady=theme.PAD_S)
        if data.from_cache:
            self._banner.configure(
                text=ru.fmt_data_cached(data.cached_at), text_color=theme.colour("warn")
            )
        else:
            self._banner.configure(text="", text_color=theme.colour("warn"))
        self._refresh_button.configure(state="normal")

    def show_error(self, text_key: str) -> None:
        self._banner.configure(text=ru.text_for(text_key), text_color=theme.colour("error"))
        self._refresh_button.configure(state="normal")

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
    ) -> None:
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=group.name, font=fonts.body, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=(theme.PAD_S, 0), pady=(theme.PAD_XS, 0)
        )
        ctk.CTkLabel(
            self,
            text=ellipsize(group.url, _URL_DISPLAY_LIMIT),
            font=fonts.small,
            text_color=theme.colour("muted"),
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=(theme.PAD_S, 0), pady=(0, theme.PAD_XS))

        ctk.CTkLabel(self, text=group_state_text(group.enabled), font=fonts.small, anchor="e").grid(
            row=0, column=1, rowspan=2, padx=theme.PAD_S
        )

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, sticky="e", padx=theme.PAD_S)
        self._edit = ctk.CTkButton(
            actions,
            text=ru.ACTION_EDIT,
            width=90,
            font=fonts.small,
            command=lambda: on_edit(group),
            **theme.secondary_button(),
        )
        self._edit.pack(side="left", padx=theme.PAD_XS)
        self._toggle = ctk.CTkButton(
            actions,
            text=toggle_action_text(group.enabled),
            width=110,
            font=fonts.small,
            command=lambda: on_toggle(group),
        )
        self._toggle.pack(side="left", padx=theme.PAD_XS)
        self._delete = ctk.CTkButton(
            actions,
            text=ru.ACTION_DELETE,
            width=90,
            font=fonts.small,
            fg_color=theme.colour("error"),
            hover_color=theme.colour("error"),
            command=lambda: on_delete(group),
        )
        self._delete.pack(side="left", padx=theme.PAD_XS)

        self._hint = ctk.CTkLabel(
            self,
            text="",
            font=fonts.small,
            text_color=theme.colour("error"),
            anchor="w",
            justify="left",
            wraplength=720,
        )
        self._hint.grid(row=2, column=0, columnspan=3, sticky="ew", padx=theme.PAD_S)

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self._edit.configure(state=state)
        self._toggle.configure(state=state)
        self._delete.configure(state=state)

    def show_conflict(self) -> None:
        self._hint.configure(text=ru.ERR_CONFLICT_GROUP_IN_USE)
