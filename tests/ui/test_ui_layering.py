"""Architecture guard: the UI package must not reach into transport/storage/secret layers."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import market_monitor_gui

pytestmark = pytest.mark.unit

_UI_ROOT = Path(market_monitor_gui.__file__).parent / "ui"

#: Import prefixes the UI package must not use (no httpx, no SQLite, no secret store).
_FORBIDDEN_PREFIXES = (
    "httpx",
    "market_monitor_gui.db",
    "market_monitor_gui.api.transport",
    "market_monitor_gui.config.secret_store",
    "cryptography",
)


def _ui_sources() -> list[Path]:
    return sorted(_UI_ROOT.rglob("*.py"))


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_ui_has_sources_to_scan() -> None:
    assert _ui_sources()


def test_ui_does_not_import_forbidden_layers() -> None:
    offenders: list[str] = []
    for path in _ui_sources():
        for module in _imported_modules(path):
            if module.startswith(_FORBIDDEN_PREFIXES):
                offenders.append(f"{path.relative_to(_UI_ROOT)}: {module}")
    assert not offenders, "UI package imports forbidden layers:\n" + "\n".join(offenders)
