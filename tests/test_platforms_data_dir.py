"""G2: per-user data directory resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from market_monitor_gui.platforms import _constants, ensure_data_dir, executable_dir, linux, windows
from market_monitor_gui.platforms import data_dir as resolve_data_dir

pytestmark = pytest.mark.unit


def test_env_override_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "custom"
    monkeypatch.setenv(_constants.DATA_DIR_ENV, str(target))
    assert resolve_data_dir() == target


def test_env_override_expands_user(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(_constants.DATA_DIR_ENV, "~/appdata")
    assert resolve_data_dir() == tmp_path / "appdata"


def test_linux_uses_xdg_data_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(_constants.DATA_DIR_ENV, raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    assert linux.data_dir() == tmp_path / "xdg" / _constants.APP_DIR_NAME


def test_linux_falls_back_to_local_share(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert linux.data_dir() == tmp_path / ".local" / "share" / _constants.APP_DIR_NAME


def test_windows_uses_local_appdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    assert windows.data_dir() == tmp_path / "LocalAppData" / _constants.APP_DIR_NAME


def test_windows_falls_back_to_home_appdata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert windows.data_dir() == tmp_path / "AppData" / "Local" / _constants.APP_DIR_NAME


def test_data_dir_is_not_created_by_pure_lookup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "not-yet"
    monkeypatch.setenv(_constants.DATA_DIR_ENV, str(target))
    _ = resolve_data_dir()
    assert not target.exists()


def test_ensure_data_dir_creates_with_owner_only_permissions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "nested" / "data"
    monkeypatch.setenv(_constants.DATA_DIR_ENV, str(target))
    created = ensure_data_dir()
    assert created == target
    assert created.is_dir()
    if created.stat().st_mode & 0o777 != 0o700:
        pytest.fail("data directory must be owner-only on POSIX")


def test_executable_dir_is_absolute() -> None:
    assert executable_dir().is_absolute()
