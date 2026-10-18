"""Application entry point.

Intentionally free of UI imports: the Tk toolkit is only imported once the
CustomTkinter shell exists (screens batch), so that command-line diagnostics and
the unit test suite never require a display.
"""

from pydantic import ValidationError

from market_monitor_gui import __version__
from market_monitor_gui.config.settings import AppSettings
from market_monitor_gui.config.urls import DEFAULT_API_BASE_URL


def main() -> None:
    """Run the GUI application.

    The CustomTkinter shell is wired in a later batch; until then this prints a
    short identity line so ``python -m market_monitor_gui`` is verifiable.
    """
    try:
        origin = AppSettings().api_base_url
    except ValidationError:
        origin = DEFAULT_API_BASE_URL
    print(f"Market Monitor {__version__} API={origin}")


if __name__ == "__main__":
    main()
