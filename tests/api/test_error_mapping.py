"""G4: HTTP/transport failures mapped to safe, classified errors."""

from __future__ import annotations

import httpx
import pytest

from market_monitor_gui.api.errors import (
    ERROR_TEXT_KEYS,
    ApiError,
    ErrorKind,
    kind_for_status,
)
from market_monitor_gui.texts import ru

from .conftest import MakeClient

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("status", "kind"),
    [
        (400, ErrorKind.VALIDATION),
        (401, ErrorKind.UNAUTHORIZED),
        (403, ErrorKind.FORBIDDEN),
        (404, ErrorKind.NOT_FOUND),
        (409, ErrorKind.CONFLICT),
        (422, ErrorKind.VALIDATION),
        (429, ErrorKind.RATE_LIMIT),
        (500, ErrorKind.SERVER),
        (503, ErrorKind.SERVER),
        (418, ErrorKind.VALIDATION),
    ],
)
def test_status_mapping(status: int, kind: ErrorKind) -> None:
    assert kind_for_status(status) is kind


def test_401_problem_json(make_client: MakeClient) -> None:
    body = {
        "type": "about:blank",
        "title": "Unauthorized",
        "status": 401,
        "detail": "Authentication required",
        "instance": "/api/v1/groups",
    }
    client = make_client(
        lambda request: httpx.Response(
            401, json=body, headers={"content-type": "application/problem+json"}
        )
    )
    with pytest.raises(ApiError) as excinfo:
        client.list_groups()
    error = excinfo.value
    assert error.kind is ErrorKind.UNAUTHORIZED
    assert error.status_code == 401
    assert error.text_key == "ERR_UNAUTHORIZED"
    assert ru.text_for(error.text_key) == ru.ERR_UNAUTHORIZED
    assert error.detail == "Authentication required"


def test_422_validation_fields(make_client: MakeClient) -> None:
    body = {
        "detail": [
            {
                "loc": ["body", "price_drop_threshold_percent"],
                "msg": "Input should be less than or equal to 100",
                "type": "less_than_equal",
                "input": 123,
            }
        ]
    }
    client = make_client(lambda request: httpx.Response(422, json=body))
    with pytest.raises(ApiError) as excinfo:
        client.get_settings()
    error = excinfo.value
    assert error.kind is ErrorKind.VALIDATION
    assert error.text_key == "ERR_VALIDATION"
    assert len(error.field_errors) == 1
    field = error.field_errors[0]
    assert field.loc == ("body", "price_drop_threshold_percent")
    assert field.code == "less_than_equal"
    assert "less than or equal" in field.message


def test_409_maps_to_conflict(make_client: MakeClient) -> None:
    client = make_client(lambda request: httpx.Response(409, json={"detail": "in use"}))
    with pytest.raises(ApiError) as excinfo:
        client.delete_group(1)
    assert excinfo.value.kind is ErrorKind.CONFLICT
    assert excinfo.value.text_key == "ERR_CONFLICT"


def test_429_maps_to_rate_limit(make_client: MakeClient) -> None:
    client = make_client(lambda request: httpx.Response(429, json={"detail": "slow down"}))
    with pytest.raises(ApiError) as excinfo:
        client.list_groups()
    assert excinfo.value.kind is ErrorKind.RATE_LIMIT


def test_non_json_error_body_still_classifies(make_client: MakeClient) -> None:
    client = make_client(lambda request: httpx.Response(500, text="<html>bad gateway</html>"))
    with pytest.raises(ApiError) as excinfo:
        client.list_groups()
    error = excinfo.value
    assert error.kind is ErrorKind.SERVER
    assert error.detail is None
    assert "bad gateway" not in str(error)


def test_timeout_maps_to_timeout(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    client = make_client(handler)
    with pytest.raises(ApiError) as excinfo:
        client.list_groups()
    assert excinfo.value.kind is ErrorKind.TIMEOUT
    assert excinfo.value.text_key == "ERR_TIMEOUT"


def test_connect_error_maps_to_network(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    client = make_client(handler)
    with pytest.raises(ApiError) as excinfo:
        client.check_auth()
    error = excinfo.value
    assert error.kind is ErrorKind.NETWORK
    assert error.status_code is None
    assert error.text_key == "ERR_NETWORK"


def test_invalid_json_on_success_maps_to_decode(make_client: MakeClient) -> None:
    client = make_client(lambda request: httpx.Response(200, text="not json"))
    with pytest.raises(ApiError) as excinfo:
        client.list_groups()
    assert excinfo.value.kind is ErrorKind.DECODE
    assert excinfo.value.text_key == "ERR_BAD_RESPONSE"


def test_wrong_shape_on_success_maps_to_decode(make_client: MakeClient) -> None:
    client = make_client(lambda request: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(ApiError) as excinfo:
        client.get_settings()
    assert excinfo.value.kind is ErrorKind.DECODE


def test_error_str_never_leaks_body(make_client: MakeClient) -> None:
    secret_leak = "super-secret-value"
    client = make_client(lambda request: httpx.Response(500, json={"detail": secret_leak}))
    with pytest.raises(ApiError) as excinfo:
        client.list_groups()
    assert secret_leak not in str(excinfo.value)
    assert secret_leak not in repr(excinfo.value)


def test_every_error_kind_has_a_russian_text_key() -> None:
    for kind in ErrorKind:
        key = ERROR_TEXT_KEYS[kind]
        assert ru.text_for(key)
