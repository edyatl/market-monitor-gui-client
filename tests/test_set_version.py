"""G18: the release helper turns git tags into the single package version."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "set_version.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("set_version", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["set_version"] = module
    spec.loader.exec_module(module)
    return module


set_version = _load_script()


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("v0.1.0", "0.1.0"),
        ("0.1.0", "0.1.0"),
        ("V1.2.3", "1.2.3"),
        ("v01.02.03", "1.2.3"),
        ("v1.0.0-alpha", "1.0.0a0"),
        ("v1.0.0-alpha.2", "1.0.0a2"),
        ("v1.0.0-beta", "1.0.0b0"),
        ("v1.0.0-beta.3", "1.0.0b3"),
        ("v1.0.0-rc.1", "1.0.0rc1"),
        ("v1.0.0rc1", "1.0.0rc1"),
        ("v1.0.0a0", "1.0.0a0"),
        ("v1.0.0b2", "1.0.0b2"),
        ("  v0.2.0  ", "0.2.0"),
    ],
)
def test_normalize_version(tag: str, expected: str) -> None:
    assert set_version.normalize_version(tag) == expected


@pytest.mark.parametrize(
    "tag",
    ["", "1.2", "v1", "release-1.2.3", "v1.2.3.4", "v1.2.3-ga", "v1.2.3-alpha.x", "latest"],
)
def test_normalize_version_rejects_unknown_tags(tag: str) -> None:
    with pytest.raises(set_version.VersionError):
        set_version.normalize_version(tag)


def test_read_and_write_version(tmp_path: Path) -> None:
    init = tmp_path / "__init__.py"
    init.write_text(
        '"""Package."""\n\n__version__ = "0.1.0"\n\n__all__ = ["__version__"]\n',
        encoding="utf-8",
    )

    assert set_version.read_version(init) == "0.1.0"
    set_version.write_version("2.3.4", init)

    assert set_version.read_version(init) == "2.3.4"
    text = init.read_text(encoding="utf-8")
    assert '__version__ = "2.3.4"' in text
    assert '__all__ = ["__version__"]' in text
    assert text.startswith('"""Package."""')


def test_write_version_requires_the_marker(tmp_path: Path) -> None:
    init = tmp_path / "__init__.py"
    init.write_text('"""No version here."""\n', encoding="utf-8")

    with pytest.raises(set_version.VersionError):
        set_version.write_version("1.0.0", init)

    with pytest.raises(set_version.VersionError):
        set_version.read_version(init)


def test_cli_print_does_not_touch_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    init = tmp_path / "__init__.py"
    init.write_text('__version__ = "0.1.0"\n', encoding="utf-8")

    assert set_version.main(["v1.0.0-rc.2", "--print", "--path", str(init)]) == 0

    assert capsys.readouterr().out.strip() == "1.0.0rc2"
    assert set_version.read_version(init) == "0.1.0"


def test_cli_writes_the_version(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    init = tmp_path / "__init__.py"
    init.write_text('__version__ = "0.1.0"\n', encoding="utf-8")

    assert set_version.main(["v0.2.0", "--path", str(init)]) == 0

    assert "0.2.0" in capsys.readouterr().out
    assert set_version.read_version(init) == "0.2.0"


def test_cli_get_and_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    init = tmp_path / "__init__.py"
    init.write_text('__version__ = "9.9.9"\n', encoding="utf-8")

    assert set_version.main(["--get", "--path", str(init)]) == 0
    assert capsys.readouterr().out.strip() == "9.9.9"

    assert set_version.main(["--get", "--print", "--path", str(init)]) == 2
    assert "--get and --print" in capsys.readouterr().err

    assert set_version.main(["--path", str(init)]) == 2
    assert "release tag is required" in capsys.readouterr().err

    assert set_version.main(["nope", "--path", str(init)]) == 2
    assert "Unsupported release tag" in capsys.readouterr().err
    assert set_version.read_version(init) == "9.9.9"


def test_repository_version_is_readable() -> None:
    version = set_version.read_version()
    assert version == set_version.normalize_version(version)
