"""Package-relative application icons and best-effort window-icon application.

The icon files are package data (``market_monitor_gui/assets/icons``), so they are
resolved relative to this module instead of the working directory. That keeps the same
paths valid for ``python -m market_monitor_gui``, editable installs, and frozen builds
that ship package data next to the package.

Everything here is best-effort: a missing or unreadable asset must never stop the GUI from
starting. ``PIL``/``CTkImage`` is deliberately not used (no extra dependency); Tk 8.6
loads PNG files natively.
"""

from __future__ import annotations

import contextlib
import logging
import sys
import tkinter as tk
import weakref
from pathlib import Path

logger = logging.getLogger(__name__)

APP_ICON_NAME = "app.ico"
APP_ICON_PNG_NAME = "app-256.png"
LOGO_SIZE = 64
_LOGO_SUBSAMPLE = 4

#: CustomTkinter overwrites a ``CTkToplevel`` icon with its own default about 200 ms
#: after creation (see ``customtkinter/windows/ctk_toplevel.py``). Re-applying ours
#: once after that is the only reliable fix on Windows.
_CTK_ICON_OVERRIDE_DELAY_MS = 350

_missing_assets_logged: set[Path] = set()
# Tk keeps only the image name; hold the Python object while the window exists.
_window_photos: weakref.WeakKeyDictionary[tk.Misc, tk.PhotoImage] = weakref.WeakKeyDictionary()


def icons_dir() -> Path:
    """Return the icons directory inside the installed package (never the CWD)."""
    return Path(__file__).resolve().parent.parent / "assets" / "icons"


def icon_path(name: str) -> Path:
    """Return the package-relative path of the icon called ``name``."""
    return icons_dir() / name


def app_icon_path() -> Path:
    """Return the Windows window/exe icon (``app.ico``)."""
    return icon_path(APP_ICON_NAME)


def app_icon_png_path() -> Path:
    """Return the cross-platform window/About icon (``app-256.png``)."""
    return icon_path(APP_ICON_PNG_NAME)


def _log_missing(path: Path) -> None:
    if path in _missing_assets_logged:
        return
    _missing_assets_logged.add(path)
    logger.info("Application icon is missing (%s); continuing without it", path)


def load_photo(path: Path) -> tk.PhotoImage | None:
    """Load ``path`` as a Tk image, or return ``None`` when it cannot be loaded."""
    if not path.is_file():
        _log_missing(path)
        return None
    try:
        return tk.PhotoImage(file=str(path))
    except (tk.TclError, OSError) as exc:
        logger.debug("Cannot load image %s: %s", path, exc)
        return None


def app_logo_photo() -> tk.PhotoImage | None:
    """Return the ``LOGO_SIZE`` px About logo, or ``None`` when the PNG is unavailable.

    Tk only supports integer subsampling, hence the quarter-scale of the 256 px source.
    """
    photo = load_photo(app_icon_png_path())
    if photo is None:
        return None
    return photo.subsample(_LOGO_SUBSAMPLE)


def apply_window_icon(window: tk.Tk | tk.Toplevel) -> bool:
    """Set the application icon on ``window``; return ``False`` when unavailable.

    Windows uses the native ``.ico`` via ``wm iconbitmap`` (which also stops
    CustomTkinter from substituting its own default icon); other platforms use the PNG
    via ``wm iconphoto``. Neither path raises.

    Dialogs need one extra step on Windows: ``CTkToplevel`` schedules its own default
    icon ~200 ms after creation, so a toplevel icon is re-applied after that delay.
    """
    if not _apply_icon(window):
        return False
    if sys.platform == "win32" and isinstance(window, tk.Toplevel):
        _schedule_icon_refresh(window)
    return True


def _apply_icon(window: tk.Tk | tk.Toplevel) -> bool:
    if sys.platform == "win32":
        path = app_icon_path()
        if not path.is_file():
            _log_missing(path)
            return False
        try:
            window.iconbitmap(str(path))
        except tk.TclError as exc:
            logger.debug("Cannot apply window icon %s: %s", path, exc)
            return False
        return True

    photo = load_photo(app_icon_png_path())
    if photo is None:
        return False
    try:
        window.iconphoto(True, photo)
    except tk.TclError as exc:
        logger.debug("Cannot apply window icon: %s", exc)
        return False
    # Tk keeps only the image name; hold the Python object for the window's lifetime.
    _window_photos[window] = photo
    return True


def _schedule_icon_refresh(window: tk.Toplevel) -> None:
    """Re-apply the icon after CustomTkinter's own icon timer fires."""
    with contextlib.suppress(tk.TclError):
        window.after(_CTK_ICON_OVERRIDE_DELAY_MS, lambda: _refresh_icon(window))


def _refresh_icon(window: tk.Toplevel) -> None:
    try:
        if not window.winfo_exists():
            return
    except tk.TclError:
        return
    _apply_icon(window)
