"""G14: button styling is never hardcoded outside the theme role helpers."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_UI_ROOT = Path(__file__).resolve().parents[2] / "src" / "market_monitor_gui" / "ui"

#: Styling that must come from ``theme.*_button()`` rather than a literal at the call site.
_BANNED_KEYWORDS = frozenset(
    {"fg_color", "hover_color", "text_color", "text_color_disabled", "corner_radius"}
)


def _button_calls(tree: ast.AST) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "CTkButton":
            calls.append(node)
    return calls


def test_every_button_uses_a_role_helper_and_no_direct_colours() -> None:
    failures: list[str] = []
    checked = 0
    for path in sorted(_UI_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for call in _button_calls(tree):
            checked += 1
            direct = sorted(
                keyword.arg for keyword in call.keywords if keyword.arg in _BANNED_KEYWORDS
            )
            if direct:
                failures.append(f"{path.name}:{call.lineno} sets {direct}")
            if not any(keyword.arg is None for keyword in call.keywords):
                failures.append(f"{path.name}:{call.lineno} has no role helper")

    assert checked > 0, "the scan found no CTkButton calls"
    assert not failures, "hardcoded button styling:\n" + "\n".join(failures)
