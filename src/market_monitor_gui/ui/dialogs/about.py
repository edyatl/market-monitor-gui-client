"""About dialog: application name, version, and logo."""

from __future__ import annotations

import warnings

import customtkinter as ctk

from market_monitor_gui import __version__
from market_monitor_gui.texts import ru
from market_monitor_gui.ui import icons, theme
from market_monitor_gui.ui.dialogs.base import BaseDialog


class AboutDialog(BaseDialog):
    """Read-only name/version dialog."""

    def __init__(self, master: ctk.CTk, *, fonts: theme.Fonts) -> None:
        super().__init__(master, title=ru.ABOUT_TITLE, fonts=fonts)

        title_pady = (theme.CONTENT_GUTTER, theme.FIELD_GAP)
        logo = icons.app_logo_photo()
        if logo is not None:
            self._logo = logo
            with warnings.catch_warnings():
                # Pillow is not a dependency, so CTkImage is unavailable; a plain Tk image
                # is fixed-size and only triggers CTk's HighDPI advice, not a real issue.
                warnings.simplefilter("ignore", UserWarning)
                ctk.CTkLabel(self, text="", image=logo).pack(
                    anchor="w",
                    padx=theme.CONTENT_GUTTER,
                    pady=(theme.CONTENT_GUTTER, 0),
                )
            title_pady = (theme.FIELD_GAP, theme.FIELD_GAP)

        ctk.CTkLabel(self, text=ru.APP_NAME, font=self.fonts.title, anchor="w").pack(
            fill="x", padx=theme.CONTENT_GUTTER, pady=title_pady
        )
        ctk.CTkLabel(self, text=ru.fmt_version(__version__), font=self.fonts.body, anchor="w").pack(
            fill="x", padx=theme.CONTENT_GUTTER, pady=(0, theme.CONTENT_GUTTER)
        )

        ctk.CTkButton(
            self,
            text=ru.ACTION_CLOSE,
            command=self.close,
            **theme.secondary_button(),
        ).pack(anchor="e", padx=theme.CONTENT_GUTTER, pady=(0, theme.CONTENT_GUTTER))
