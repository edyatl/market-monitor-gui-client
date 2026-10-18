"""Map transport/session exceptions to ``texts/ru.py`` keys.

The GUI layers never render raw exception text: a screen asks this module for a text
key and resolves it through :func:`market_monitor_gui.texts.ru.text_for`. The mapping
is pure (no I/O, no widgets) so it is unit-testable without a display.
"""

from __future__ import annotations

from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.texts import ru


def text_key_for_exception(exc: BaseException) -> str:
    """Return the ``ru`` text key to show for ``exc``.

    API/transport failures already carry a ``text_key``; anything else falls back to
    the generic message so no raw exception ever reaches the operator.
    """
    if isinstance(exc, ApiError):
        return exc.text_key
    return ru.ERR_UNEXPECTED


def login_failure_text_key(exc: BaseException) -> str:
    """Return the login-dialog message for a failed sign-in attempt.

    A ``401`` means the secret was rejected (distinct from a missing secret), so it
    maps to the dedicated login-failure text.
    """
    if isinstance(exc, ApiError) and exc.kind is ErrorKind.UNAUTHORIZED:
        return ru.LOGIN_FAILED
    return text_key_for_exception(exc)
