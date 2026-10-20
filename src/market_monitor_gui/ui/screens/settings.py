"""Settings screen: edit the single global price-drop threshold.

Rendering plus callbacks only: the shell fetches and writes through services on the
task runner. The field accepts a comma or a dot decimal separator and is validated
locally with Russian messages before the shell performs the PATCH. All operator text
comes from :mod:`market_monitor_gui.texts.ru`.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from market_monitor_gui.services.settings import SettingsData
from market_monitor_gui.texts import ru
from market_monitor_gui.ui import theme
from market_monitor_gui.ui.banner import Banner, BannerKind
from market_monitor_gui.ui.controls import set_button_enabled
from market_monitor_gui.ui.forms import parse_threshold_percent
from market_monitor_gui.ui.screens.base import ScreenFrame
from market_monitor_gui.ui.settings_view import format_threshold


class SettingsScreen(ScreenFrame):
    """A single-field form for the global threshold with inline feedback."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        *,
        fonts: theme.Fonts,
        on_refresh: Callable[[], None],
        on_save: Callable[[float], None],
    ) -> None:
        super().__init__(master, title=ru.SIDEBAR_SETTINGS, fonts=fonts)
        self._on_save = on_save
        self._on_refresh = on_refresh
        self._value = tk.StringVar()
        self._loading = False
        self._busy = False
        self._read_only = False

        threshold_label = ctk.CTkLabel(
            self.body, text=ru.LABEL_THRESHOLD, font=fonts.body, anchor="w"
        )
        self._banner = Banner(
            self.body,
            fonts=fonts,
            wraplength=640,
            pady=(0, theme.SECTION_GAP),
            before=threshold_label,
        )
        threshold_label.pack(fill="x")
        self._entry = ctk.CTkEntry(self.body, textvariable=self._value, width=200)
        self._entry.pack(anchor="w", pady=(theme.FIELD_GAP, theme.FIELD_BOTTOM))
        self._entry.bind("<Return>", self._on_return)

        ctk.CTkLabel(
            self.body,
            text=ru.SETTINGS_THRESHOLD_HINT,
            font=fonts.small,
            text_color=theme.colour("muted"),
            wraplength=640,
            justify="left",
            anchor="w",
        ).pack(fill="x")

        buttons = ctk.CTkFrame(self.body, fg_color="transparent")
        buttons.pack(fill="x", pady=theme.SECTION_GAP)
        self._save_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_SAVE,
            command=self._submit,
            **theme.primary_button(),
        )
        self._save_button.pack(side="left")
        self._refresh_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_REFRESH,
            command=on_refresh,
            **theme.secondary_button(),
        )
        self._refresh_button.pack(side="left", padx=theme.TOOLBAR_GAP)

        self._status = ctk.CTkLabel(
            self.body,
            text="",
            font=fonts.small,
            text_color=theme.colour("muted"),
            wraplength=640,
            justify="left",
            anchor="w",
        )
        self._status.pack(fill="x")

    # -- state ----------------------------------------------------------------

    def set_loading(self) -> None:
        self._loading = True
        self._banner.show(BannerKind.LOADING, ru.SETTINGS_LOADING)
        self._apply_state()

    def render(self, data: SettingsData) -> None:
        """Show the fetched threshold; label cached (offline) values with a time."""
        self._value.set(format_threshold(data.price_drop_threshold_percent))
        self._read_only = data.from_cache
        if data.from_cache:
            self._banner.show(BannerKind.CACHED, ru.fmt_data_cached_readonly(data.cached_at))
        else:
            self._banner.clear()
        self._status.configure(text="")
        self._loading = False
        self._busy = False
        self._apply_state()

    def show_read_error(self, text_key: str) -> None:
        """The read failed: report it and lock the form until a successful read."""
        self._read_only = True
        self._loading = False
        self._busy = False
        self._banner.show(
            BannerKind.ERROR,
            ru.fmt_readonly_notice(ru.text_for(text_key)),
            on_action=self._on_refresh,
        )
        self._apply_state()

    def show_saved(self, value: float) -> None:
        """Show the server-confirmed value and a success message."""
        self._value.set(format_threshold(value))
        self._status.configure(text=ru.SETTINGS_SAVED, text_color=theme.colour("ok"))
        self._busy = False
        self._apply_state()

    def show_write_error(self, text_key: str) -> None:
        """A save failed: report it but keep the form usable for a retry."""
        self._status.configure(text=ru.text_for(text_key), text_color=theme.colour("error"))
        self._busy = False
        self._apply_state()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._apply_state()

    def _apply_state(self) -> None:
        editable = not (self._loading or self._busy or self._read_only)
        self._entry.configure(state="normal" if editable else "disabled")
        set_button_enabled(self._save_button, editable, theme.primary_button())
        set_button_enabled(
            self._refresh_button,
            not (self._loading or self._busy),
            theme.secondary_button(),
        )

    # -- callbacks ------------------------------------------------------------

    def on_show(self) -> None:
        """The shell refreshes the value when the screen is shown."""

    def _on_return(self, _event: object) -> None:
        self._submit()

    def _submit(self) -> None:
        result = parse_threshold_percent(self._value.get())
        if result.value is None:
            self._status.configure(
                text=ru.text_for(result.error or "ERR_VALIDATION"),
                text_color=theme.colour("error"),
            )
            return
        self._status.configure(text="")
        self.set_busy(True)
        self._on_save(result.value)
