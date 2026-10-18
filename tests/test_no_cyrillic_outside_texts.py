"""Guard: Russian operator text lives only in ``texts/ru.py``."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import market_monitor_gui

pytestmark = pytest.mark.unit

_CYRILLIC = re.compile(r"[\u0400-\u04ff]")

_PACKAGE_ROOT = Path(market_monitor_gui.__file__).parent
_ALLOWED = {(_PACKAGE_ROOT / "texts" / "ru.py").resolve()}


def _package_sources() -> list[Path]:
    return [path for path in _PACKAGE_ROOT.rglob("*.py") if path.resolve() not in _ALLOWED]


def test_package_has_sources_to_scan() -> None:
    assert _package_sources()


def test_no_cyrillic_outside_texts_ru() -> None:
    offenders: list[str] = []
    for path in _package_sources():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _CYRILLIC.search(line):
                offenders.append(f"{path.relative_to(_PACKAGE_ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, "Cyrillic text outside texts/ru.py:\n" + "\n".join(offenders)
