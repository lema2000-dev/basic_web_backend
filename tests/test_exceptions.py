import pytest

from basic_web_backend.exceptions import (
    BackendError,
    RoutingError,
    DuplicateRouteError,
    HTTPException,
    NotFound,
    MethodNotAllowed,
)

def test_routing_error_is_backend_error():
    assert issubclass(RoutingError, BackendError)

def test_duplicate_route_error_is_routing_error():
    assert issubclass(DuplicateRouteError, RoutingError)

def test_duplicate_route_error_preserves_message():
    error = DuplicateRouteError(
        "Route GET /users already registered."
    )
    assert str(error) == "Route GET /users already registered."

def test_http_exception_is_backend_error():
    assert issubclass(HTTPException, BackendError)

def test_not_found_has_http_error_information():
    error = NotFound("/missing")

    assert isinstance(error, HTTPException)
    assert error.status_code == 404
    assert error.reason == "Not Found"
    assert str(error) == "No route was found for path: /missing"

def test_method_not_allowed_has_http_error_information():
    error = MethodNotAllowed("POST", "/users", ["GET", "PUT"])

    assert isinstance(error, HTTPException)
    assert error.status_code == 405
    assert error.reason == "Method Not Allowed"
    assert error.method == "POST"
    assert error.path == "/users"
    assert str(error) == "Method POST is not allowed for path: /users."
    assert error.allowed_methods == ("GET", "PUT")

def test_method_not_allowed_normalizes_method_name():
    error = MethodNotAllowed("post", "/users", ["get", "put"])

    assert error.method == "POST"
    assert error.allowed_methods == ("GET", "PUT")

def test_http_exception_uses_default_message():
    error = HTTPException(500, "Internal Server Error")

    assert str(error) == "500 Internal Server Error"

def test_http_exception_uses_custom_message():
    error = HTTPException(400, "Bad Request", message="Custom error message")

    assert str(error) == "Custom error message"

