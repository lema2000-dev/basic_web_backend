import json

import pytest

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
    text_response

)

def test_content_response_returns():
    result = content_response(body="<messege>Hello</messege>", content_type="application/xml", status_code=201,
        headers={"X-Custom-Header": "Custom Value"}) 

    assert result == ("<messege>Hello</messege>", 201, {"X-Custom-Header": "Custom Value", "Content-Type": "application/xml"})

def test_html_response_returns():
    result = html_response(body="<h1>Hello</h1>", status_code=200, headers={"X-Custom-Header": "Custom Value"})

    assert result == ("<h1>Hello</h1>", 200, {"X-Custom-Header": "Custom Value", "Content-Type": "text/html; charset=utf-8"})

def test_text_response_returns():
    result = text_response(body="Hello", status_code=200, headers={"X-Custom-Header": "Custom Value"})

    assert result == ("Hello", 200, {"X-Custom-Header": "Custom Value", "Content-Type": "text/plain; charset=utf-8"})

def test_json_response_returns():
    data = {"message": "Hello", "active": True}
    body, status_code, headers = json_response(data=data, status_code=200, headers={"X-Custom-Header": "Custom Value"})

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
    assert result == ("", status_code, {"X-Custom-Header": "Custom Value", "Content-Type": None, "Location": "/new-location"})

def test_redirect_response_rejects_invalid_status_code():
    with pytest.raises(ValueError, match="Invalid redirect status code: 200"):
        redirect_response(location="/new-location", status_code=200)

def test_empty_response_returns():
    result = empty_response(status_code=204, headers={"X-Custom-Header": "Custom Value"})
    assert result == (b"", 204, {"X-Custom-Header": "Custom Value", "Content-Type": None})


