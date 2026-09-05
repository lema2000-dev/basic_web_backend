import json
import pytest
from http.cookies import SimpleCookie

from basic_web_backend.response import (
    MIME_TYPES,
    REDIRECT_STATUS_CODES,
    content_response,
    empty_response,
    file_response,
    guess_content_type,
    html_response,
    json_response,
    redirect_response,
    text_response,
    set_cookie
)

def test_content_response_returns():
    result = content_response(body="<messege>Hello</messege>", content_type="application/xml", status_code=201,
        headers={"X-Custom-Header": "Custom Value"}) 

    assert result == ("<messege>Hello</messege>", 201, {"X-Custom-Header": "Custom Value", "Content-Type": "application/xml"})

def test_html_response_returns():
    result = html_response(body="<h1>Hello</h1>", status_code=200, headers={"X-Custom-Header": "Custom Value"})

    result = (result[0].decode("utf-8"), result[1], result[2])  # Decode the body for comparison

    assert result == ("<h1>Hello</h1>", 200, {"X-Custom-Header": "Custom Value", "Content-Type": "text/html; charset=utf-8"})

def test_text_response_returns():
    result = text_response(body="Hello", status_code=200, headers={"X-Custom-Header": "Custom Value"})

    result = (result[0].decode("utf-8"), result[1], result[2])  # Decode the body for comparison

    assert result == ("Hello", 200, {"X-Custom-Header": "Custom Value", "Content-Type": "text/plain; charset=utf-8"})

def test_json_response_returns():
    data = {"message": "Hello", "active": True}
    body, status_code, headers = json_response(data=data, status_code=200, headers={"X-Custom-Header": "Custom Value"})

    body = body.decode("utf-8")

    assert body == json.dumps(data, ensure_ascii=False)
    assert status_code == 200
    assert headers == {"X-Custom-Header": "Custom Value", "Content-Type": "application/json; charset=utf-8"}

@pytest.mark.parametrize("extension, expected_content_type", MIME_TYPES.items())
def test_guess_content_type_known_extensions(extension, expected_content_type):
    filename = f"file{extension.upper()}"
    assert guess_content_type(filename) == expected_content_type

def test_guess_content_type_unknown_extension():
    filename = "file.unknown"
    assert guess_content_type(filename) == "application/octet-stream"

def test_file_response_reads_file_as_bytes(tmp_path):
    file_content = "Hello, World!"
    file_path = tmp_path / "test.txt"
    file_path.write_bytes(file_content.encode())

    body, status_code, headers = file_response(file_path=file_path)

    assert body == file_content.encode()
    assert status_code == 200
    assert headers == {"Content-Type": "text/plain"}

def test_file_response_creates_attachment_header(tmp_path):
    file_content = "PDF content"
    file_path = tmp_path / "report.pdf"
    file_path.write_bytes(file_content.encode())

    body, status_code, headers = file_response(file_path=file_path, as_attachment=True, download_name="downloaded-report.pdf")

    assert body == file_content.encode()
    assert status_code == 200
    assert headers == {"Content-Type": "application/pdf", "Content-Disposition": "attachment; filename=\"downloaded-report.pdf\""}

def test_file_response_creates_attachment_header_with_default_filename(tmp_path):
    file_content = "PDF content"
    file_path = tmp_path / "report.pdf"
    file_path.write_bytes(file_content.encode())

    body, status_code, headers = file_response(file_path=file_path, as_attachment=True)

    assert body == file_content.encode()
    assert status_code == 200
    assert headers == {"Content-Type": "application/pdf", "Content-Disposition": "attachment; filename=\"report.pdf\""}

def test_file_response_creates_attachment_header_with_safe_filename(tmp_path):
    file_content = "PDF content"
    file_path = tmp_path / "report.pdf"
    file_path.write_bytes(file_content.encode())

    body, status_code, headers = file_response(file_path=file_path, as_attachment=True, download_name='folder/unsafe"\r\nname.pdf')

    assert body == file_content.encode()
    assert status_code == 200
    assert headers == {"Content-Type": "application/pdf", "Content-Disposition": "attachment; filename=\"unsafe___name.pdf\""}

@pytest.mark.parametrize("status_code", REDIRECT_STATUS_CODES)
def test_redirect_response_accepts_valid_status_codes(status_code):
    result = redirect_response(location="/new-location", status_code=status_code, headers={"X-Custom-Header": "Custom Value"})
    assert result == ("", status_code, {"X-Custom-Header": "Custom Value", "Location": "/new-location"})

def test_redirect_response_rejects_invalid_status_code():
    with pytest.raises(ValueError, match="Invalid redirect status code: 200"):
        redirect_response(location="/new-location", status_code=200)

def test_empty_response_returns():
    result = empty_response(status_code=204, headers={"X-Custom-Header": "Custom Value"})
    assert result == (b"", 204, {"X-Custom-Header": "Custom Value"})

@pytest.mark.parametrize(
    ("response_factory", "content_type"),
    [
        (
            html_response,
            "text/html; charset=utf-16",
        ),
        (
            text_response,
            "text/plain; charset=utf-16",
        ),
    ],
)
def test_text_responses_support_custom_charset(
    response_factory,
    content_type,
):
    body, status_code, headers = (
        response_factory(
            "Hello, world!",
            charset="utf-16",
        )
    )

    assert isinstance(body, bytes)
    assert body.decode("utf-16") == (
        "Hello, world!"
    )
    assert status_code == 200
    assert headers["Content-Type"] == content_type

def test_json_response_supports_custom_charset():
    body, status_code, headers = json_response(
        {
            "message": "Hello, world!",
            "successful": True,
        },
        charset="utf-16",
    )

    assert isinstance(body, bytes)

    decoded_body = body.decode("utf-16")

    assert '"message": "Hello, world!"' in (
        decoded_body
    )
    assert '"successful": true' in decoded_body
    assert status_code == 200
    assert headers["Content-Type"] == (
        "application/json; charset=utf-16"
    )

def test_set_cookie_adds_cookie_header():
    response = json_response(
        {"authenticated": True}
    )

    body, status_code, headers = set_cookie(
        response=response,
        key="session_id",
        value="abc123",
        max_age=3600,
        path="/",
        secure=True,
        http_only=True,
        same_site="Lax",
    )

    cookie_headers = [
        value
        for name, value in headers
        if name.lower() == "set-cookie"
    ]

    assert len(cookie_headers) == 1

    cookie = SimpleCookie()
    cookie.load(cookie_headers[0])

    morsel = cookie["session_id"]

    assert morsel.value == "abc123"
    assert morsel["max-age"] == "3600"
    assert morsel["path"] == "/"
    assert morsel["secure"] is True
    assert morsel["httponly"] is True
    assert morsel["samesite"] == "Lax"

def test_set_cookie_preserves_multiple_cookies():
    response = text_response("Cookies created")

    response = set_cookie(
        response=response,
        key="session_id",
        value="abc123",
    )

    response = set_cookie(
        response=response,
        key="theme",
        value="dark",
    )

    body, status_code, headers = response

    cookie_headers = [
        value
        for name, value in headers
        if name.lower() == "set-cookie"
    ]

    assert len(cookie_headers) == 2

    cookies = SimpleCookie()

    for header in cookie_headers:
        cookies.load(header)

    assert cookies["session_id"].value == (
        "abc123"
    )
    assert cookies["theme"].value == "dark"

def test_set_cookie_does_not_mutate_original_headers():
    original_response = html_response(
        "<h1>Hello</h1>"
    )

    original_headers = original_response[2]

    set_cookie(
        response=original_response,
        key="theme",
        value="dark",
    )

    assert original_headers == {
        "Content-Type": (
            "text/html; charset=utf-8"
        ),
    }