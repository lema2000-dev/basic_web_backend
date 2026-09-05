import pytest

from basic_web_backend.exceptions import BadRequest
from basic_web_backend.multipart import UploadedFile, parse_multipart

def test_parse_multipart_extracts_text_field():
    body = (
        b"--ExampleBoundary\r\n"
        b'Content-Disposition: form-data; name="username"\r\n'
        b"\r\n"
        b"Martin\r\n"
        b"--ExampleBoundary--\r\n"
    )

    form, files = parse_multipart(body=body, boundary="ExampleBoundary")

    assert form == {"username": ["Martin"]}
    assert files == {}

def test_parse_multipart_extracts_uploaded_file():
    body = (
        b"--ExampleBoundary\r\n"
        b'Content-Disposition: form-data; name="avatar"; '
        b'filename="profile.png"\r\n'
        b"Content-Type: image/png\r\n"
        b"\r\n"
        b"\x89PNG\r\nx00binary-data\r\n"
        b"--ExampleBoundary--\r\n"
    )

    form, files = parse_multipart(body=body, boundary="ExampleBoundary")

    assert form == {}
    assert list(files.keys()) == ["avatar"]

    uploaded_file = files["avatar"][0]
    assert isinstance(uploaded_file, UploadedFile)
    assert uploaded_file.filename == "profile.png"
    assert uploaded_file.content_type == "image/png"
    assert uploaded_file.body == b"\x89PNG\r\nx00binary-data"

def test_parse_multipart_extracts_fields_and_files():
    body = (
        b"--ExampleBoundary\r\n"
        b'Content-Disposition: form-data; name="description"\r\n'
        b"\r\n"
        b"Profile image\r\n"
        b"--ExampleBoundary\r\n"
        b'Content-Disposition: form-data; name="avatar"; '
        b'filename="profile.png"\r\n'
        b"Content-Type: image/png\r\n"
        b"\r\n"
        b"\x89PNG\r\nx00binary-data\r\n"
        b"--ExampleBoundary--\r\n"
    )

    form, files = parse_multipart(body=body, boundary="ExampleBoundary")

    assert form == {"description": ["Profile image"]}
    assert files["avatar"][0].filename == "profile.png"
    assert files["avatar"][0].body == b"\x89PNG\r\nx00binary-data"

def test_parse_multipart_preserves_repeated_fields():
    body = (
        b"--ExampleBoundary\r\n"
        b'Content-Disposition: form-data; '
        b'name="color"\r\n'
        b"\r\n"
        b"red\r\n"
        b"--ExampleBoundary\r\n"
        b'Content-Disposition: form-data; '
        b'name="color"\r\n'
        b"\r\n"
        b"blue\r\n"
        b"--ExampleBoundary--\r\n"
    )

    form, files = parse_multipart(body=body, boundary="ExampleBoundary")

    assert form == {"color": ["red", "blue"]}
    assert files == {}

def test_parse_multipart_preserves_repeated_files():
    body = (
        b"--ExampleBoundary\r\n"
        b'Content-Disposition: form-data; name="documents"; '
        b'filename="first.txt"\r\n'
        b"Content-Type: text/plain\r\n"
        b"\r\n"
        b"First document content\r\n"
        b"--ExampleBoundary\r\n"
        b'Content-Disposition: form-data; name="documents"; '
        b'filename="second.txt"\r\n'
        b"Content-Type: text/plain\r\n"
        b"\r\n"
        b"Second document content\r\n"
        b"--ExampleBoundary--\r\n"
    )

    form, files = parse_multipart(body=body, boundary="ExampleBoundary")

    assert form == {}
    assert [file.filename for file in files["documents"]] == ["first.txt", "second.txt"]

def test_parse_multipart_rejects_non_bytes_body():
    with pytest.raises(BadRequest):
        parse_multipart(body="not bytes", boundary="ExampleBoundary")

def test_parse_multipart_rejects_empty_boundary():
    with pytest.raises(BadRequest):
        parse_multipart(body=b"", boundary="")

    