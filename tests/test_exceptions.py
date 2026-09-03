import pytest

from basic_web_backend.exceptions import (
    BackendError,
    RoutingError,
    DuplicateRouteError,
    HTTPException,
    NotFound,
    MethodNotAllowed,
    BadRequest,
    Conflict,
    Forbidden,
    PayloadTooLarge,
    Unauthorized,
    UnprocessableContent,
    UnsupportedMediaType
)

def test_routing_error_is_backend_error():
    assert issubclass(RoutingError, BackendError)

def test_duplicate_route_error_is_routing_error():
    assert issubclass(DuplicateRouteError, RoutingError)

def test_duplicate_route_error_preserves_message():
    error = DuplicateRouteError(
        path="/users",
        method="GET"
    )
    assert str(error) == "Route alredy registered for path: /users and method: GET"

def test_not_found_has_http_error_information():
    error = NotFound("/missing", "No route was found for path: /missing")

    assert isinstance(error, HTTPException)
    assert error.status_code == 404
    assert str(error) == "No route was found for path: /missing"
    assert error.message == "No route was found for path: /missing"

def test_method_not_allowed_has_http_error_information():
    error = MethodNotAllowed("POST", "/users", ["GET", "PUT"])

    assert isinstance(error, HTTPException)
    assert error.status_code == 405
    assert error.method == "POST"
    assert error.path == "/users"
    assert str(error) == "Method Not Allowed"
    assert error.allowed_methods == ("GET", "PUT")

def test_method_not_allowed_normalizes_method_name():
    error = MethodNotAllowed("post", "/users", ["get", "put"])

    assert error.method == "POST"
    assert error.allowed_methods == ("GET", "PUT")

def test_http_exception_uses_default_message():
    error = HTTPException()

    assert str(error) == "Internal Server Error"

def test_http_exception_uses_custom_message():
    error = HTTPException(message="Custom error message")

    assert str(error) == "Custom error message"

@pytest.mark.parametrize(
    (
        "exception_class",
        "expected_status_code",
        "expected_message",
    ),
    [
        (BadRequest, 400, "Bad Request"),
        (Unauthorized, 401, "Unauthorized"),
        (Forbidden, 403, "Forbidden"),
        (Conflict, 409, "Conflict"),
        (
            PayloadTooLarge,
            413,
            "Payload Too Large",
        ),
        (
            UnsupportedMediaType,
            415,
            "Unsupported Media Type",
        ),
        (
            UnprocessableContent,
            422,
            "Unprocessable Content",
        ),
    ],
)
def test_http_exception_default_values(
    exception_class,
    expected_status_code,
    expected_message,
):
    error = exception_class()

    assert error.status_code == expected_status_code
    assert error.message == expected_message
    assert error.headers == {}
    assert str(error) == expected_message

def test_http_exception_accepts_custom_message_and_headers():
    error = Unauthorized(
        message="Authentication is required.",
        headers={
            "WWW-Authenticate": "Basic",
        },
    )

    assert error.status_code == 401
    assert error.message == (
        "Authentication is required."
    )
    assert error.headers == {
        "WWW-Authenticate": "Basic",
    }