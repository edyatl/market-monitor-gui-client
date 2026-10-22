"""G19: connection dialog secret surface and save values (needs a display)."""

from __future__ import annotations

import os
import tkinter as tk
from typing import Any

import pytest

from market_monitor_gui.texts import ru
from market_monitor_gui.ui.forms import ConnectionFormValues

pytestmark = pytest.mark.e2e


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


requires_display = pytest.mark.skipif(not _has_display(), reason="no display available")

ORIGIN = "https://api.test.example"


def _walk(widget: tk.Misc) -> list[tk.Misc]:
    found: list[tk.Misc] = []
    for child in widget.winfo_children():
        found.append(child)
        found.extend(_walk(child))
    return found


def _open(**kwargs: Any) -> tuple[Any, Any]:
    import customtkinter as ctk

    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.dialogs.connection import ConnectionDialog

    root = ctk.CTk()
    dialog = ConnectionDialog(
        root,
        fonts=theme.build_fonts(),
        initial_origin=ORIGIN,
        on_save=kwargs.pop("on_save", lambda _values: None),
        **kwargs,
    )
    root.update()
    return root, dialog


@requires_display
def test_secret_saved_state_shows_placeholder_and_enables_forget() -> None:
    root, dialog = _open(secret_saved=True)
    try:
        assert dialog._secret_entry.cget("placeholder_text") == ru.CONN_SECRET_PLACEHOLDER
        assert str(dialog._secret_state.cget("text")) == ru.CONN_SECRET_SAVED
        assert dialog._forget_button.cget("state") == "normal"
        assert bool(dialog._save_secret.get()) is True
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_no_stored_secret_hides_placeholder_and_disables_forget() -> None:
    root, dialog = _open(secret_saved=False)
    try:
        assert dialog._secret_entry.cget("placeholder_text") == ""
        assert str(dialog._secret_state.cget("text")) == ru.CONN_SECRET_NOT_SAVED
        assert dialog._forget_button.cget("state") == "disabled"
        assert bool(dialog._save_secret.get()) is False
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_env_override_is_surfaced() -> None:
    import customtkinter as ctk

    root, dialog = _open(secret_saved=False, env_secret=True)
    try:
        texts = [
            str(widget.cget("text")) for widget in _walk(dialog) if isinstance(widget, ctk.CTkLabel)
        ]
        assert ru.CONN_SECRET_ENV_NOTE in texts
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_forget_button_calls_the_shell() -> None:
    calls: list[bool] = []
    root, dialog = _open(secret_saved=True, on_forget=lambda: calls.append(True))
    try:
        dialog._forget()
        assert calls == [True]
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_save_submits_origin_secret_and_remember() -> None:
    submitted: list[ConnectionFormValues] = []
    root, dialog = _open(secret_saved=False, on_save=submitted.append)
    try:
        dialog._secret.set("typed-secret")
        dialog._save_secret.set(True)
        dialog._save()
        assert submitted == [
            ConnectionFormValues(origin=ORIGIN, secret="typed-secret", remember=True)
        ]
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_set_secret_saved_after_forget_clears_the_field() -> None:
    root, dialog = _open(secret_saved=True)
    try:
        dialog._secret.set("typed-secret")
        dialog.set_secret_saved(False)
        root.update()
        assert dialog._secret.get() == ""
        assert str(dialog._secret_state.cget("text")) == ru.CONN_SECRET_NOT_SAVED
        assert dialog._forget_button.cget("state") == "disabled"
        assert bool(dialog._save_secret.get()) is False
    finally:
        dialog.close()
        root.destroy()
