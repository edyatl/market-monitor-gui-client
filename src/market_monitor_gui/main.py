"""Application entry point.

``--version`` stays free of UI imports so diagnostics work without a display. The
CustomTkinter shell (and thus Tk) is imported only when the GUI is launched.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from market_monitor_gui import __version__
from market_monitor_gui.texts import ru


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-monitor-gui")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the GUI, or print the version when ``--version`` is given."""
    args = _build_parser().parse_args(argv)
    if args.version:
        print(f"{ru.APP_NAME} {__version__}")
        return 0
    return _run_gui()


def _run_gui() -> int:
    import tkinter as tk

    from market_monitor_gui.app import AppContext
    from market_monitor_gui.ui.app import Shell

    context = AppContext.create()
    try:
        shell = Shell(context)
    except tk.TclError:
        print(ru.ERR_NO_DISPLAY, file=sys.stderr)
        context.close()
        return 2
    shell.start()
    shell.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
