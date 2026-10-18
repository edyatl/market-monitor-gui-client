"""Safe, typed error model for API calls.

Errors never carry a secret, a cookie, a raw HTTP body, or English API text that
would be shown to the operator. They carry a :class:`ErrorKind` and a ``text_key``
naming a constant in :mod:`market_monitor_gui.texts.ru`; the UI resolves the key to
Russian text. Raw server ``detail``/validation messages are kept for diagnostics
only and must not be displayed directly.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class ErrorKind(StrEnum):
    """Classification of API failures, mapped to operator text by the UI."""

    NETWORK = "network"
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    VALIDATION = "validation"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    DECODE = "decode"


#: Default Russian text key (constant name in ``texts/ru.py``) per error kind.
ERROR_TEXT_KEYS: Final[Mapping[ErrorKind, str]] = {
    ErrorKind.NETWORK: "ERR_NETWORK",
    ErrorKind.TIMEOUT: "ERR_TIMEOUT",
    ErrorKind.UNAUTHORIZED: "ERR_UNAUTHORIZED",
    ErrorKind.FORBIDDEN: "ERR_FORBIDDEN",
    ErrorKind.NOT_FOUND: "ERR_NOT_FOUND",
    ErrorKind.VALIDATION: "ERR_VALIDATION",
    ErrorKind.CONFLICT: "ERR_CONFLICT",
    ErrorKind.RATE_LIMIT: "ERR_RATE_LIMIT",
    ErrorKind.SERVER: "ERR_SERVER",
    ErrorKind.DECODE: "ERR_BAD_RESPONSE",
}

_STATUS_KINDS: Final[Mapping[int, ErrorKind]] = {
    400: ErrorKind.VALIDATION,
    401: ErrorKind.UNAUTHORIZED,
    403: ErrorKind.FORBIDDEN,
    404: ErrorKind.NOT_FOUND,
    409: ErrorKind.CONFLICT,
    422: ErrorKind.VALIDATION,
    429: ErrorKind.RATE_LIMIT,
}


@dataclass(frozen=True, slots=True)
class FieldError:
    """A single server-side validation error for one field."""

    loc: tuple[str | int, ...]
    code: str
    message: str


class ApiError(Exception):
    """A classified API failure.

    Attributes:
        kind: coarse classification used to pick operator text and retry policy.
        text_key: name of the constant in ``texts/ru.py`` to render.
        status_code: HTTP status when the failure came from a response, else ``None``.
        field_errors: per-field validation errors (empty unless the server sent them).
        method: HTTP method of the failed request (diagnostics).
        path: request path/URL of the failed request (diagnostics; never a secret).
        detail: raw server message for diagnostics only; never displayed to operators.
    """

    def __init__(
        self,
        kind: ErrorKind,
        *,
        text_key: str | None = None,
        status_code: int | None = None,
        field_errors: tuple[FieldError, ...] = (),
        method: str | None = None,
        path: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.kind = kind
        self.text_key = text_key if text_key is not None else ERROR_TEXT_KEYS[kind]
        self.status_code = status_code
        self.field_errors = field_errors
        self.method = method
        self.path = path
        self.detail = detail
        super().__init__(f"{kind.value} http={status_code} {method} {path}".rstrip())


def kind_for_status(status_code: int) -> ErrorKind:
    """Map an HTTP status code to an :class:`ErrorKind`."""
    if status_code in _STATUS_KINDS:
        return _STATUS_KINDS[status_code]
    if status_code >= 500:
        return ErrorKind.SERVER
    if 400 <= status_code < 500:
        return ErrorKind.VALIDATION
    return ErrorKind.SERVER


def parse_field_errors(body: object) -> tuple[FieldError, ...]:
    """Extract FastAPI validation errors (``{"detail": [ ... ]}``)."""
    if not isinstance(body, dict):
        return ()
    detail = body.get("detail")
    if not isinstance(detail, list):
        return ()
    errors: list[FieldError] = []
    for item in detail:
        if not isinstance(item, dict):
            continue
        raw_loc = item.get("loc")
        loc = (
            tuple(part for part in raw_loc if isinstance(part, (str, int)))
            if isinstance(raw_loc, list)
            else ()
        )
        errors.append(
            FieldError(
                loc=loc,
                code=str(item.get("type", "")),
                message=str(item.get("msg", "")),
            )
        )
    return tuple(errors)


def _safe_detail(body: object) -> str | None:
    if not isinstance(body, dict):
        return None
    detail = body.get("detail")
    if isinstance(detail, str):
        return detail
    title = body.get("title")
    if isinstance(title, str):
        return title
    return None


def error_from_http(
    status_code: int,
    body: object | None,
    *,
    method: str | None = None,
    path: str | None = None,
) -> ApiError:
    """Build an :class:`ApiError` from a non-success HTTP response."""
    kind = kind_for_status(status_code)
    return ApiError(
        kind,
        status_code=status_code,
        field_errors=parse_field_errors(body) if kind is ErrorKind.VALIDATION else (),
        method=method,
        path=path,
        detail=_safe_detail(body),
    )
