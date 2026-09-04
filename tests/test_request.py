import pytest

from basic_web_backend.request import Request
from basic_web_backend.exceptions import BadRequest, UnsupportedMediaType

def test_request_has_default_values():
    request = Request("GET", "/test")
    assert request.method == "GET"
    assert request.path == "/test"
    assert request.query_string == ""
    assert request.body == b""
    assert request.headers == []
    assert request.query == {}

def test_request_normalizes_method_to_uppercase():
    request = Request("post", "/test")
    assert request.method == "POST"

def test_request_preserves_path_and_body():
    body = b'{"key": "value"}'

    request = Request("POST", "/test", body=body)

    assert request.path == "/test"
    assert request.body is body

def test_request_accepts_headers_as_dict():
    headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}
    request = Request("GET", "/test", headers=headers)

    assert request.headers == [
        ("content-type", "application/json"),
        ("authorization", "Bearer token")
    ]

def test_request_preservers_repeated_headers():
    headers = [("Content-Type", "application/json"), ("Content-Type", "text/plain")]
    request = Request("GET", "/test", headers=headers)

    assert request.headers == [
        ("content-type", "application/json"),
        ("content-type", "text/plain")
    ]

def test_get_header_is_case_insensitive():
    headers = {"Content-Type": "application/json"}
    request = Request("GET", "/test", headers=headers)

    assert request.get_header("content-type") == "application/json"
    assert request.get_header("CONTENT-TYPE") == "application/json"
    assert request.get_header("Content-Type") == "application/json"

def test_get_header_returns_first_repeated_value():
    headers = [("Content-Type", "application/json"), ("Content-Type", "text/plain")]
    request = Request("GET", "/test", headers=headers)

    assert request.get_header("content-type") == "application/json"

def test_get_header_returns_default_for_missing_header():
    request = Request("GET", "/test")

    assert request.get_header("missing-header", default="default-value") == "default-value"
    assert request.get_header("missing-header") is None

def test_get_headers_returns_all_matching_values():
    headers = [("Content-Type", "application/json"), ("Content-Type", "text/plain")]
    request = Request("GET", "/test", headers=headers)

    assert request.get_headers("content-type") == ["application/json", "text/plain"]
    assert request.get_headers("missing-header") == []

def test_request_preserves_repeated_query_parameters():
    query_string = "param=value1&param=value2&other=single"
    request = Request("GET", "/test", query_string=query_string)

    assert request.query == {
        "param": ["value1", "value2"],
        "other": ["single"]
    }

def test_request_preserves_blank_query_values():
    query_string = "param=&other=single"
    request = Request("GET", "/test", query_string=query_string)

    assert request.query == {
        "param": [""],
        "other": ["single"]
    }

def test_request_decodes_query_parameters():
    query_string = "messege=Hello+World%21"
    request = Request("GET", "/test", query_string=query_string)

    assert request.query == {
        "messege": ["Hello World!"]
    }

def test_request_extracts_normalised_content_type_and_charset():
    request = Request(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": (
                "Application/JSON; Charset=UTF-8"
            ),
        },
        body=b'{"name": "Martin"}',
    )

    assert request.content_type == (
        "application/json"
    )

    assert request.charset == "utf-8"

def test_request_extracts_content_type_parameters():
    request = Request(
        method="POST",
        path="/upload",
        headers={
            "Content-Type": (
                "multipart/form-data; "
                "boundary=example-boundary; "
                "charset=utf-8"
            ),
        },
    )

    assert request.content_type == (
        "multipart/form-data"
    )
    assert request.charset == "utf-8"

def test_request_has_no_content_type_without_header():
    request = Request(
        method="POST",
        path="/api/users",
    )

    assert request.content_type is None
    assert request.charset is None

def test_request_has_no_explicit_charset():
    request = Request(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": "application/json",
        },
    )

    assert request.content_type == (
        "application/json"
    )
    assert request.charset is None

def test_request_extracts_quoted_charset():
    request = Request(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": (
                'application/json; charset="utf-8"'
            ),
        },
    )

    assert request.charset == "utf-8"

def test_request_parses_json_body():
    request = Request(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": "application/json",
        },
        body=(
            b'{"name": "Martin", "active": true}'
        ),
    )

    assert request.get_json() == {
        "name": "Martin",
        "active": True,
    }

def test_request_decodes_json_as_utf8_by_default():
    body = (
        '{"message": "Welcome, José!"}'
        .encode("utf-8")
    )

    request = Request(
        method="POST",
        path="/api/messages",
        headers={
            "Content-Type": "application/json",
        },
        body=body,
    )

    assert request.get_json() == {
        "message": "Welcome, José!",
    }

def test_request_uses_explicit_json_charset():
    body = (
        '{"message": "Hello"}'
        .encode("utf-16")
    )

    request = Request(
        method="POST",
        path="/api/messages",
        headers={
            "Content-Type": (
                "application/json; charset=utf-16"
            ),
        },
        body=body,
    )

    assert request.get_json() == {
        "message": "Hello",
    }

def test_request_accepts_json_based_media_type():
    request = Request(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": (
                "application/vnd.example.user+json"
            ),
        },
        body=b'{"name": "Martin"}',
    )

    assert request.get_json() == {
        "name": "Martin",
    }

def test_get_json_rejects_non_json_content_type():
    request = Request(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": "text/plain",
        },
        body=b'{"name": "Martin"}',
    )

    with pytest.raises(
        UnsupportedMediaType
    ):
        request.get_json()

def test_get_json_rejects_invalid_json():
    request = Request(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": "application/json",
        },
        body=b'{"name": }',
    )

    with pytest.raises(BadRequest):
        request.get_json()

def test_get_json_rejects_invalid_character_encoding():
    request = Request(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": (
                "application/json; charset=utf-8"
            ),
        },
        body=b'{"name": "\xff"}',
    )

    with pytest.raises(BadRequest):
        request.get_json()

def test_request_parses_urlencoded_form():
    request = Request(
        method="POST",
        path="/login",
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        },
        body=(
            b"username=Martin"
            b"&city=New+York"
        ),
    )

    assert request.get_form() == {
        "username": ["Martin"],
        "city": ["New York"],
    }

def test_request_decodes_urlencoded_form_values():
    request = Request(
        method="POST",
        path="/messages",
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        },
        body=b"message=Hello%2C+world%21",
    )

    assert request.get_form() == {
        "message": ["Hello, world!"],
    }

def test_request_preserves_repeated_form_fields():
    request = Request(
        method="POST",
        path="/preferences",
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        },
        body=(
            b"color=red"
            b"&color=green"
            b"&color=blue"
        ),
    )

    assert request.get_form() == {
        "color": [
            "red",
            "green",
            "blue",
        ],
    }

def test_request_preserves_blank_form_values():
    request = Request(
        method="POST",
        path="/profile",
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        },
        body=b"display_name=",
    )

    assert request.get_form() == {
        "display_name": [""],
    }

def test_request_parses_empty_form_body():
    request = Request(
        method="POST",
        path="/form",
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        },
        body=b"",
    )

    assert request.get_form() == {}

def test_get_form_rejects_wrong_content_type():
    request = Request(
        method="POST",
        path="/form",
        headers={
            "Content-Type": "application/json",
        },
        body=b'{"name": "Martin"}',
    )

    with pytest.raises(
        UnsupportedMediaType
    ):
        request.get_form()

def test_get_form_rejects_invalid_character_encoding():
    request = Request(
        method="POST",
        path="/form",
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded; "
                "charset=utf-8"
            ),
        },
        body=b"name=\xff",
    )

    with pytest.raises(BadRequest):
        request.get_form()

def test_request_parses_cookies():
    request = Request(
        method="GET",
        path="/profile",
        headers={
            "Cookie": (
                "session=abc123; theme=dark"
            ),
        },
    )

    assert request.cookies == {
        "session": "abc123",
        "theme": "dark",
    }

def test_request_ignores_whitespace_around_cookies():
    request = Request(
        method="GET",
        path="/profile",
        headers={
            "Cookie": (
                "session=abc123;   theme=dark"
            ),
        },
    )

    assert request.cookies == {
        "session": "abc123",
        "theme": "dark",
    }

def test_request_parses_quoted_cookie_value():
    request = Request(
        method="GET",
        path="/profile",
        headers={
            "Cookie": 'message="Hello world"',
        },
    )

    assert request.cookies == {
        "message": "Hello world",
    }

def test_request_has_empty_cookies_without_header():
    request = Request(
        method="GET",
        path="/profile",
    )

    assert request.cookies == {}

def test_request_combines_multiple_cookie_headers():
    request = Request(
        method="GET",
        path="/profile",
        headers=[
            ("Cookie", "session=abc123"),
            ("Cookie", "theme=dark"),
        ],
    )

    assert request.cookies == {
        "session": "abc123",
        "theme": "dark",
    }

def test_request_preserves_encoded_cookie_value():
    request = Request(
        method="GET",
        path="/profile",
        headers={
            "Cookie": "value=Hello%20world",
        },
    )

    assert request.cookies == {
        "value": "Hello%20world",
    }

def test_request_ignores_invalid_cookie_header():
    request = Request(
        method="GET",
        path="/",
        headers={
            "Cookie": (
                'session="unterminated'
            ),
        },
    )

    assert request.cookies == {}