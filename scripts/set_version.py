"""Align the package version with a release tag.

Release builds take the version from the annotated git tag (``v0.1.0``), never from a
hand-edited constant. CI runs this script on the checked-out tree before freezing; the
mutation is intentionally **not** committed.

``src/market_monitor_gui/__init__.py::__version__`` is the single source of truth: the
runtime UI, ``--version``, the User-Agent, and the wheel metadata (hatchling reads the
same constant) all follow it.

Examples::

    python scripts/set_version.py v0.1.0 --print    # print "0.1.0", change nothing
    python scripts/set_version.py v0.1.0            # rewrite __version__
    python scripts/set_version.py --get             # print the current version
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

DEFAULT_INIT_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "market_monitor_gui" / "__init__.py"
)

_VERSION_PATTERN = re.compile(r"^__version__\s*=\s*(['\"])(?P<version>[^'\"]*)\1\s*$", re.MULTILINE)

_TAG_RE = re.compile(
    r"^[vV]?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:[-.]?(?P<stage>alpha|beta|pre|preview|rc|a|b|c)(?:[.-]?(?P<number>\d+))?)?$"
)

_STAGE_ALIASES = {
    "alpha": "a",
    "a": "a",
    "beta": "b",
    "b": "b",
    "c": "rc",
    "pre": "rc",
    "preview": "rc",
    "rc": "rc",
}


class VersionError(ValueError):
    """Raised when a tag cannot be turned into a PEP 440 release version."""


def normalize_version(tag: str) -> str:
    """Return the PEP 440 version for a release tag (``v1.0.0-alpha`` -> ``1.0.0a0``)."""
    value = tag.strip()
    match = _TAG_RE.match(value)
    if match is None:
        raise VersionError(
            f"Unsupported release tag {tag!r}: expected vX.Y.Z "
            "(optionally -alpha/-beta/-rc[.N]), e.g. v0.1.0 or v1.0.0-rc.1"
        )
    version = f"{int(match['major'])}.{int(match['minor'])}.{int(match['patch'])}"
    stage = match["stage"]
    if stage is not None:
        version += f"{_STAGE_ALIASES[stage.lower()]}{int(match['number'] or 0)}"
    return version


def read_version(path: Path = DEFAULT_INIT_PATH) -> str:
    """Read ``__version__`` from the package ``__init__`` file."""
    match = _VERSION_PATTERN.search(path.read_text(encoding="utf-8"))
    if match is None:
        raise VersionError(f"{path} has no __version__ assignment")
    return match.group("version")


def write_version(version: str, path: Path = DEFAULT_INIT_PATH) -> None:
    """Rewrite the ``__version__`` assignment, leaving the rest of the file untouched."""
    source = path.read_text(encoding="utf-8")
    replacement = f'__version__ = "{version}"'
    updated, count = _VERSION_PATTERN.subn(replacement, source)
    if count != 1:
        raise VersionError(f"{path} must contain exactly one __version__ assignment, found {count}")
    path.write_text(updated, encoding="utf-8", newline="\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Set the package version from a release tag.")
    parser.add_argument("tag", nargs="?", help="release tag, e.g. v0.1.0")
    parser.add_argument(
        "--print",
        dest="print_only",
        action="store_true",
        help="print the normalized version without changing any file",
    )
    parser.add_argument(
        "--get",
        action="store_true",
        help="print the current package version without changing any file",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_INIT_PATH,
        help="package __init__.py to read/write (defaults to the repository source tree)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI; return the process exit code."""
    args = _build_parser().parse_args(argv)
    if args.get and args.print_only:
        print("--get and --print are mutually exclusive", file=sys.stderr)
        return 2
    if args.get:
        print(read_version(args.path))
        return 0
    if args.tag is None:
        print("a release tag is required unless --get is used", file=sys.stderr)
        return 2
    try:
        version = normalize_version(args.tag)
    except VersionError as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.print_only:
        print(version)
        return 0
    try:
        write_version(version, args.path)
    except VersionError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(f"package version set to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
