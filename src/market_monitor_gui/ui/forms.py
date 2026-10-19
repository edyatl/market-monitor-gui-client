"""Tk-free form validation and outcome helpers.

Keeping this logic out of the widgets lets the login/connection paths be unit-tested
without a display, and keeps operator text in :mod:`market_monitor_gui.texts.ru`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from market_monitor_gui.config.urls import (
    is_default_origin,
    is_loopback_origin,
    normalize_api_origin,
)
from market_monitor_gui.services.errors import login_failure_text_key
from market_monitor_gui.texts import ru


@dataclass(frozen=True, slots=True)
class OriginInput:
    """Result of validating an API origin field.

    Exactly one of ``origin`` (valid) or ``error`` (invalid) is set. ``warning`` may
    accompany a valid origin and is non-blocking.
    """

    origin: str | None
    error: str | None
    warning: str | None


#: Group name max length, mirroring the API contract (server remains authoritative).
GROUP_NAME_MAX_LEN: Final[int] = 200


@dataclass(frozen=True, slots=True)
class GroupFormValues:
    """Trimmed, validated group form values ready for the API."""

    name: str
    url: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class GroupFormResult:
    """Result of validating the group editor form.

    Exactly one of ``values`` (valid) or ``error`` (a ``ru`` text key) is set.
    """

    values: GroupFormValues | None
    error: str | None


def validate_group_form(name: str, url: str, enabled: bool) -> GroupFormResult:
    """Lightly validate the group editor fields; the server stays authoritative."""
    clean_name = name.strip()
    clean_url = url.strip()
    if not clean_name:
        return GroupFormResult(None, ru.GROUP_NAME_REQUIRED)
    if len(clean_name) > GROUP_NAME_MAX_LEN:
        return GroupFormResult(None, ru.GROUP_NAME_TOO_LONG)
    if not clean_url:
        return GroupFormResult(None, ru.GROUP_URL_REQUIRED)
    if not _looks_like_http_url(clean_url):
        return GroupFormResult(None, ru.GROUP_URL_INVALID)
    return GroupFormResult(GroupFormValues(clean_name, clean_url, enabled), None)


def _looks_like_http_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("http://", "https://"))


def validate_origin_input(raw: str) -> OriginInput:
    """Normalize and classify a user-entered API origin.

    ``http://`` is accepted for loopback hosts without warning; for any other host it
    is accepted with :data:`ru.CONN_WRN_NOT_HTTPS` as a warning (never a hard block).
    """
    try:
        origin = normalize_api_origin(raw)
    except ValueError:
        return OriginInput(None, ru.CONN_ORIGIN_INVALID, None)
    return OriginInput(origin, None, _origin_warning(origin))


def _origin_warning(origin: str) -> str | None:
    if origin.startswith("http://") and not is_loopback_origin(origin):
        return ru.CONN_WRN_NOT_HTTPS
    return None


def custom_origin_warning(origin: str) -> str | None:
    """Return a warning when ``origin`` is not the built-in production address."""
    return None if is_default_origin(origin) else ru.CONN_CUSTOM_ORIGIN_WARNING


def validate_secret_input(raw: str) -> str | None:
    """Return an error text key for ``raw``, or ``None`` when it is usable."""
    return None if raw.strip() else ru.ERR_SECRET_REQUIRED


def login_error_text(exc: BaseException) -> str:
    """Return the login-dialog message key for a failed sign-in."""
    return login_failure_text_key(exc)
