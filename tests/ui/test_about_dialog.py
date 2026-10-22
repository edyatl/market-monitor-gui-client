"""G17: the About dialog shows the 64 px logo when the PNG asset is available."""

from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.unit


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _walk(widget: tk.Misc) -> list[tk.Misc]:
    found: list[tk.Misc] = []
    for child in widget.winfo_children():
        found.append(child)
        found.extend(_walk(child))
    return found


def _open_about() -> tuple[Any, Any]:
    import customtkinter as ctk

    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.dialogs.about import AboutDialog

    root = ctk.CTk()
    dialog = AboutDialog(root, fonts=theme.build_fonts())
    root.update()
    return root, dialog


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_about_dialog_shows_the_logo_and_version() -> None:
    import customtkinter as ctk

    from market_monitor_gui import __version__
    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui import icons

    root, dialog = _open_about()
    try:
        labels = [widget for widget in _walk(dialog) if isinstance(widget, ctk.CTkLabel)]
        logos = [label for label in labels if label.cget("image") is not None]
        assert len(logos) == 1
        photo = logos[0].cget("image")
        assert (photo.width(), photo.height()) == (icons.LOGO_SIZE, icons.LOGO_SIZE)

        texts = [str(label.cget("text")) for label in labels]
        assert ru.APP_NAME in texts
        assert ru.fmt_version(__version__) in texts
    finally:
        dialog.close()
        root.destroy()


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_about_dialog_opens_without_the_logo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import customtkinter as ctk

    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui import icons

    monkeypatch.setattr(icons, "icons_dir", lambda: tmp_path)
    root, dialog = _open_about()
    try:
        labels = [widget for widget in _walk(dialog) if isinstance(widget, ctk.CTkLabel)]
        assert not [label for label in labels if label.cget("image") is not None]
        assert ru.APP_NAME in [str(label.cget("text")) for label in labels]
        assert dialog.winfo_exists()
    finally:
        dialog.close()
        root.destroy()


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_about_dialog_opens_the_repository_link() -> None:
    import customtkinter as ctk

    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.dialogs.about import AboutDialog

    opened: list[str] = []
    root = ctk.CTk()
    dialog = AboutDialog(root, fonts=theme.build_fonts(), on_open_url=opened.append)
    root.update()
    try:
        buttons = [
            widget
            for widget in _walk(dialog)
            if isinstance(widget, ctk.CTkButton)
            and str(widget.cget("text")) == ru.ABOUT_REPOSITORY_LINK
        ]
        assert len(buttons) == 1
        buttons[0].invoke()
        assert opened == [ru.ABOUT_REPOSITORY_URL]
    finally:
        dialog.close()
        root.destroy()
