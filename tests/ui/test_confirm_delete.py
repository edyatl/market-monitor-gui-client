"""G15: the confirm-delete dialog's 409 conflict state machine (needs a display)."""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def test_app_passes_the_conflict_text_key_name() -> None:
    """The shell must pass the registered key *name*, not its Russian value."""
    app_source = (
        Path(__file__).resolve().parents[2] / "src" / "market_monitor_gui" / "ui" / "app.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(app_source, filename="app.py")

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "show_conflict"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "dialog"
    ]
    assert calls, "no show_conflict call found in app.py"
    for call in calls:
        first = call.args[0]
        assert isinstance(first, ast.Constant) and first.value == "ERR_CONFLICT_GROUP_IN_USE"


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_conflict_disables_delete_and_promotes_the_alternative() -> None:
    import customtkinter as ctk

    from market_monitor_gui.texts import ru
    from market_monitor_gui.ui import theme
    from market_monitor_gui.ui.dialogs.confirm_delete import ConfirmDeleteDialog

    root = ctk.CTk()
    dialog = ConfirmDeleteDialog(
        root,
        fonts=theme.build_fonts(),
        question=ru.fmt_confirm_delete_group("Group"),
        confirm_label=ru.ACTION_DELETE,
        on_confirm=lambda: None,
    )
    try:
        dialog.show_conflict(
            "ERR_CONFLICT_GROUP_IN_USE",
            ru.ACTION_DISABLE_GROUP,
            lambda: None,
        )
        root.update()

        assert dialog._error.cget("text") == ru.ERR_CONFLICT_GROUP_IN_USE
        assert dialog._confirm_button.cget("state") == "disabled"
        assert dialog._alternative is not None
        assert dialog._alternative.cget("state") == "normal"
        assert dialog._alternative.cget("fg_color") == theme.colour("accent")

        # The alternative sits before the (now disabled) delete button.
        siblings = dialog._confirm_button.master.pack_slaves()
        assert siblings.index(dialog._alternative) < siblings.index(dialog._confirm_button)

        # The delete button stays disabled even if a later path clears busy.
        dialog.set_busy(False)
        assert dialog._confirm_button.cget("state") == "disabled"

        # Enter can never confirm a delete: the dialog binds no Return handler.
        assert dialog.bind("<Return>") == ""
    finally:
        dialog.close()
        root.destroy()
