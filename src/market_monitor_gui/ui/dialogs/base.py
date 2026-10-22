"""Shared behaviour for modal ``CTkToplevel`` dialogs."""

from __future__ import annotations

import contextlib
import tkinter as tk

import customtkinter as ctk

from market_monitor_gui.ui import icons, theme


class BaseDialog(ctk.CTkToplevel):
    """Modal, centred, Escape-to-cancel dialog with a single close path."""

    def __init__(
        self,
        master: ctk.CTk | ctk.CTkToplevel,
        *,
        title: str,
        fonts: theme.Fonts,
        resizable: bool = False,
    ) -> None:
        super().__init__(master)
        self._fonts = fonts
        self._closed = False
        self.title(title)
        self.resizable(resizable, resizable)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", self._on_escape)
        icons.apply_window_icon(self)

    @property
    def fonts(self) -> theme.Fonts:
        """Font set shared with the shell."""
        return self._fonts

    def show_modal(self) -> None:
        """Centre the dialog and take the grab (non-blocking, so Tk keeps polling)."""
        self.update_idletasks()
        self._centre()
        self.grab_set()
        self.focus_force()

    def close(self) -> None:
        """Destroy the dialog once, releasing the grab.

        When this dialog was opened on top of another toplevel (e.g. the forget-secret
        confirmation over connection settings), the parent's modal grab is restored.
        """
        if self._closed:
            return
        self._closed = True
        master = self.master
        with contextlib.suppress(tk.TclError):
            self.grab_release()
        self.destroy()
        if isinstance(master, tk.Toplevel):
            with contextlib.suppress(tk.TclError):
                if master.winfo_exists():
                    master.grab_set()

    def _on_escape(self, _event: object) -> None:
        self.close()

    def _centre(self) -> None:
        parent = self.master
        parent.update_idletasks()
        width = int(self.winfo_reqwidth())
        height = int(self.winfo_reqheight())
        x = int(parent.winfo_rootx()) + (int(parent.winfo_width()) - width) // 2
        y = int(parent.winfo_rooty()) + (int(parent.winfo_height()) - height) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
