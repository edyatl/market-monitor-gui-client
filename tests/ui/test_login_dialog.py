"""G19: login dialog stored/manual modes (needs a display)."""

from __future__ import annotations

import os
from typing import Any

import pytest

from market_monitor_gui.texts import ru
from market_monitor_gui.ui.forms import LoginFormValues

pytestmark = pytest.mark.e2e


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


requires_display = pytest.mark.skipif(not _has_display(), reason="no display available")


def _open(*, secret_available: bool, on_submit: Any = None) -> tuple[Any, Any]:
    import customtkinter as ctk

    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.dialogs.login import LoginDialog

    root = ctk.CTk()
    dialog = LoginDialog(
        root,
        fonts=theme.build_fonts(),
        secret_available=secret_available,
        on_submit=on_submit if on_submit is not None else (lambda _values: None),
    )
    root.update()
    return root, dialog


@requires_display
def test_manual_mode_submits_the_typed_secret_and_remembers_by_default() -> None:
    submitted: list[LoginFormValues] = []
    root, dialog = _open(secret_available=False, on_submit=submitted.append)
    try:
        assert dialog._manual is True
        assert bool(dialog._remember.get()) is True
        dialog._secret.set("typed-secret")
        dialog._submit()
        assert submitted == [LoginFormValues(secret="typed-secret", remember=True)]
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_stored_mode_submits_without_a_secret() -> None:
    submitted: list[LoginFormValues] = []
    root, dialog = _open(secret_available=True, on_submit=submitted.append)
    try:
        assert dialog._manual is False
        assert dialog._entry.winfo_manager() == ""
        dialog._submit()
        assert submitted == [LoginFormValues(secret=None, remember=False)]
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_use_other_secret_switches_to_manual_mode() -> None:
    root, dialog = _open(secret_available=True)
    try:
        dialog._use_other_secret()
        root.update()
        assert dialog._manual is True
        assert dialog._entry.winfo_manager() != ""
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_show_error_flips_a_rejected_stored_secret_to_manual() -> None:
    root, dialog = _open(secret_available=True)
    try:
        dialog.show_error("LOGIN_FAILED")
        root.update()
        assert dialog._manual is True
        assert str(dialog._error.cget("text")) == ru.text_for("LOGIN_FAILED")
        assert dialog._login_button.cget("state") == "normal"
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_empty_manual_secret_is_rejected_locally() -> None:
    submitted: list[LoginFormValues] = []
    root, dialog = _open(secret_available=False, on_submit=submitted.append)
    try:
        dialog._secret.set("   ")
        dialog._submit()
        assert submitted == []
        assert str(dialog._error.cget("text")) == ru.text_for("ERR_SECRET_REQUIRED")
    finally:
        dialog.close()
        root.destroy()


@requires_display
def test_remember_checkbox_can_be_unchecked() -> None:
    submitted: list[LoginFormValues] = []
    root, dialog = _open(secret_available=False, on_submit=submitted.append)
    try:
        dialog._remember.set(False)
        dialog._secret.set("typed-secret")
        dialog._submit()
        assert submitted == [LoginFormValues(secret="typed-secret", remember=False)]
    finally:
        dialog.close()
        root.destroy()
