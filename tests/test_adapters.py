import pytest

from basic_web_server import Request as ServerRequest
from basic_web_backend.adapters import LemaRequestAdapter, LemaResponseAdapter
from basic_web_backend.request import Request

def test_lema_request_adapter_creates_backend_request():
    server_request = ServerRequest(
        b"GET /test?param=value HTTP/1.1\r\n"
        b"Host: example.com\r\n"
        b"\r\n"
    )

    adapter = LemaRequestAdapter()
    backend_request = adapter.convert(server_request)

    assert isinstance(backend_request, Request)
    assert backend_request.method == "GET"
    assert backend_request.path == "/test"
    assert backend_request.query_string == "param=value"
    assert backend_request.query == {"param": ["value"]}
    assert backend_request.headers == [("host", "example.com")]
    assert backend_request.body == b""

def test_lema_request_adapter_preserves_body():
    server_request = ServerRequest(
        b"POST /submit HTTP/1.1\r\n"
        b"Host: example.com\r\n"
        b"Content-Length: 5\r\n"
        b"\r\n"
        b"Hello"
    )

    adapter = LemaRequestAdapter()
    backend_request = adapter.convert(server_request)

    assert backend_request.body == b"Hello"
    assert backend_request.body is server_request.body  # Ensure the body is the same object

def test_lema_request_adapter_preserver_repeated_headers():
    server_request = ServerRequest(
        b"GET /test HTTP/1.1\r\n"
        b"Host: example.com\r\n"
        b"X-Custom-Header: Value1\r\n"
        b"X-Custom-Header: Value2\r\n"
        b"\r\n"
    )

    adapter = LemaRequestAdapter()
    backend_request = adapter.convert(server_request)

    assert backend_request.get_headers("X-Custom-Header") == ["Value1", "Value2"]

def test_lema_request_adapter_dose_not_return_server_request():
    server_request = ServerRequest(
        b"GET /test HTTP/1.1\r\n"
        b"Host: example.com\r\n"
        b"\r\n"
    )

    adapter = LemaRequestAdapter()
    backend_request = adapter.convert(server_request)

    assert backend_request is not server_request  # Ensure a new object is returned

def test_lema_response_adapter_preserves_three_part_response():
    backend_response = (b"Hello, World!", 200, {"Content-Type": "text/plain"})

    adapter = LemaResponseAdapter()
    server_response = adapter.convert(backend_response)

    assert server_response == backend_response

def test_lema_response_adapter_preserves_two_part_response():
    backend_response = (b"Hello, World!", 200)

    adapter = LemaResponseAdapter()
    server_response = adapter.convert(backend_response)

    assert server_response == backend_response

def test_lema_response_adapter_preserves_body_only_response():
    backend_response = b"Hello, World!"

    adapter = LemaResponseAdapter()
    server_response = adapter.convert(backend_response)

    assert server_response == backend_response

def test_lema_response_adapter_removes_content_dictionary():
    backend_response = (b"Hello, World!", 200, {"Content-Type": "text/plain", "Content-Length": "13"})

    adapter = LemaResponseAdapter()
    server_response = adapter.convert(backend_response)

    assert server_response == (b"Hello, World!", 200, {"Content-Type": "text/plain"})

def test_lema_response_adapter_preserves_repeated_headers():
    backend_response = (
        "Hello",
        200,
        [
            ("Set-Cookie", "first=1"),
            ("Content-Length", "999"),
            ("Set-Cookie", "second=2"),
        ],
    )

    adapter = LemaResponseAdapter()
    server_response = adapter.convert(backend_response)

    assert server_response == (
        "Hello",
        200,
        [
            ("Set-Cookie", "first=1"),
            ("Set-Cookie", "second=2"),
        ],
    )


def test_lema_response_adapter_does_not_modify_original_headers():
    headers = {
        "Content-Type": "text/plain",
        "Content-Length": "999",
    }

    backend_response = (
        "Hello",
        200,
        headers,
    )

    adapter = LemaResponseAdapter()
    adapter.convert(backend_response)

    assert headers == {
        "Content-Type": "text/plain",
        "Content-Length": "999",
    }

def test_response_adapter_preserves_repeated_cookies():
    adapter = LemaResponseAdapter()

    response = (
        b"Hello",
        200,
        [
            ("Content-Type", "text/plain"),
            ("Set-Cookie", "session_id=abc123"),
            ("Content-Length", "5"),
            ("Set-Cookie", "theme=dark"),
        ],
    )

    result = adapter.convert(response)

    assert result == (
        b"Hello",
        200,
        [
            ("Content-Type", "text/plain"),
            ("Set-Cookie", "session_id=abc123"),
            ("Set-Cookie", "theme=dark"),
        ],
    )