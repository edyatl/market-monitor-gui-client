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
        self._value = tk.StringVar()

        self._banner = ctk.CTkLabel(
            self.body,
            text="",
            font=fonts.small,
            text_color=theme.colour("muted"),
            wraplength=640,
            justify="left",
            anchor="w",
        )
        self._banner.pack(fill="x", pady=(0, theme.PAD_M))

        ctk.CTkLabel(self.body, text=ru.LABEL_THRESHOLD, font=fonts.body, anchor="w").pack(fill="x")
        self._entry = ctk.CTkEntry(self.body, textvariable=self._value, width=200)
        self._entry.pack(anchor="w", pady=(theme.PAD_XS, theme.PAD_XS))
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
        buttons.pack(fill="x", pady=theme.PAD_M)
        self._save_button = ctk.CTkButton(buttons, text=ru.ACTION_SAVE, command=self._submit)
        self._save_button.pack(side="left")
        self._refresh_button = ctk.CTkButton(
            buttons,
            text=ru.ACTION_REFRESH,
            command=on_refresh,
            **theme.secondary_button(),
        )
        self._refresh_button.pack(side="left", padx=theme.PAD_S)

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
        self._banner.configure(text=ru.SETTINGS_LOADING, text_color=theme.colour("muted"))
        self.set_busy(True)

    def render(self, data: SettingsData) -> None:
        """Show the fetched threshold; label cached (offline) values with a time."""
        self._value.set(format_threshold(data.price_drop_threshold_percent))
        if data.from_cache:
            self._banner.configure(
                text=ru.fmt_data_cached(data.cached_at), text_color=theme.colour("warn")
            )
        else:
            self._banner.configure(text="", text_color=theme.colour("muted"))
        self._status.configure(text="")
        self.set_busy(False)

    def show_error(self, text_key: str) -> None:
        self._banner.configure(text=ru.text_for(text_key), text_color=theme.colour("error"))
        self.set_busy(False)

    def show_saved(self, value: float) -> None:
        """Show the server-confirmed value and a success message."""
        self._value.set(format_threshold(value))
        self._status.configure(text=ru.SETTINGS_SAVED, text_color=theme.colour("ok"))
        self.set_busy(False)

    def show_save_error(self, text_key: str) -> None:
        self._status.configure(text=ru.text_for(text_key), text_color=theme.colour("error"))
        self.set_busy(False)

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self._entry.configure(state=state)
        self._save_button.configure(state=state)
        self._refresh_button.configure(state=state)

    # -- callbacks ------------------------------------------------------------

    def on_show(self) -> None:
        """The shell refreshes the value when the screen is shown."""

    def _on_return(self, _event: object) -> None:
        self._submit()

    def _submit(self) -> None:
        result = parse_threshold_percent(self._value.get())
        if result.value is None:
            self._status.configure(
                text=ru.text_for(result.error or ru.ERR_VALIDATION),
                text_color=theme.colour("error"),
            )
            return
        self._status.configure(text="")
        self.set_busy(True)
        self._on_save(result.value)
