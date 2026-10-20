"""G17: package-relative icon paths and best-effort Tk icon application."""

from __future__ import annotations

import logging
import os
import sys
import tkinter as tk
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def test_icon_paths_are_package_relative_and_present() -> None:
    import market_monitor_gui
    from market_monitor_gui.ui import icons

    package_root = Path(market_monitor_gui.__file__).resolve().parent
    assert icons.app_icon_path().name == icons.APP_ICON_NAME
    assert icons.app_icon_png_path().name == icons.APP_ICON_PNG_NAME
    for path in (icons.app_icon_path(), icons.app_icon_png_path()):
        assert path.is_relative_to(package_root)
        assert path.is_file()
    assert icons.icons_dir() == package_root / "assets" / "icons"


def test_icon_paths_do_not_depend_on_the_working_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from market_monitor_gui.ui import icons

    before = icons.app_icon_png_path()
    monkeypatch.chdir(tmp_path)
    assert icons.app_icon_png_path() == before
    assert icons.app_icon_png_path().is_file()


def test_missing_assets_are_logged_once_and_tolerated(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from market_monitor_gui.ui import icons

    monkeypatch.setattr(icons, "icons_dir", lambda: tmp_path)
    assert not icons.app_icon_path().exists()
    assert icons.icon_path("other.png") == tmp_path / "other.png"

    with caplog.at_level(logging.INFO, logger=icons.__name__):
        assert icons.load_photo(icons.app_icon_png_path()) is None
        assert icons.load_photo(icons.app_icon_png_path()) is None

    records = [record for record in caplog.records if "missing" in record.getMessage()]
    assert len(records) == 1


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_window_icon_is_applied() -> None:
    from market_monitor_gui.ui import icons

    root = tk.Tk()
    try:
        root.withdraw()
        assert icons.apply_window_icon(root) is True
        if sys.platform != "win32":
            assert root in icons._window_photos
    finally:
        root.destroy()


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_missing_window_icon_is_swallowed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from market_monitor_gui.ui import icons

    monkeypatch.setattr(icons, "icons_dir", lambda: tmp_path)
    root = tk.Tk()
    try:
        root.withdraw()
        assert icons.apply_window_icon(root) is False
        assert root.winfo_exists()
    finally:
        root.destroy()


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_broken_image_file_is_swallowed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from market_monitor_gui.ui import icons

    (tmp_path / icons.APP_ICON_PNG_NAME).write_bytes(b"not a png")
    monkeypatch.setattr(icons, "icons_dir", lambda: tmp_path)
    root = tk.Tk()
    try:
        root.withdraw()
        assert icons.load_photo(icons.app_icon_png_path()) is None
        assert icons.apply_window_icon(root) is False
    finally:
        root.destroy()


@pytest.mark.e2e
@pytest.mark.skipif(not _has_display(), reason="no display available")
def test_logo_is_quarter_scale() -> None:
    from market_monitor_gui.ui import icons

    root = tk.Tk()
    try:
        photo = icons.app_logo_photo()
        assert photo is not None
        assert (photo.width(), photo.height()) == (icons.LOGO_SIZE, icons.LOGO_SIZE)
    finally:
        root.destroy()
