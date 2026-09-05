import json
import mimetypes
from pathlib import Path
from http.cookies import SimpleCookie

MIME_TYPES = {
    #Web
    ".html": "text/html",
    ".htm": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".txt": "text/plain",
    ".xml": "application/xml",
    ".csv": "text/csv",

    #Images
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".svg": "image/svg+xml",
    ".gif": "image/gif",
    ".ico": "image/x-icon",

    #Fonts
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".otf": "font/otf",

    #Documents and archives
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".rar": "application/vnd.rar",
    ".zip": "application/zip",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",

    #Audio and video
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".mp4": "video/mp4",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".webm": "video/webm",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac"
}

REDIRECT_STATUS_CODES = {
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    307: "Temporary Redirect",
    308: "Permanent Redirect"
}

def _prepare_headers(default_content_type=None, headers=None):
    if headers is None:
        response_headers = {}
    else:
        response_headers = dict(headers)

    has_content_type = any(
        name.lower() == "content-type" for name in response_headers)

    if default_content_type and not has_content_type:
        response_headers["Content-Type"] = default_content_type

    return response_headers

def guess_content_type(filename):
    path = Path(filename)
    extension = path.suffix.lower()

    if extension in MIME_TYPES:
        return MIME_TYPES[extension]

    guessed_type, encoding = mimetypes.guess_type(path.name)
    if guessed_type is not None:
        return guessed_type

    return "application/octet-stream"

def content_response(body, content_type, status_code=200, headers=None):
    response_headers = _prepare_headers(content_type, headers)
    return body, status_code, response_headers

def html_response(body, status_code=200, headers=None, charset="utf-8"):
    encoded_body = body.encode(charset)
    return content_response(body=encoded_body, content_type=f"text/html; charset={charset}",
        status_code=status_code, headers=headers)

def text_response(body, status_code=200, headers=None, charset="utf-8"):
    encoded_body = body.encode(charset)
    return content_response(body=encoded_body, content_type=f"text/plain; charset={charset}",
        status_code=status_code, headers=headers)

def json_response(data, status_code=200, headers=None, charset="utf-8"):
    body = json.dumps(data, ensure_ascii=False)
    encoded_body = body.encode(charset)
    return content_response(body=encoded_body, content_type=f"application/json; charset={charset}",
        status_code=status_code, headers=headers)

def file_response(file_path, status_code=200, headers=None, as_attachment=False, download_name=None):
    path = Path(file_path)
    body = path.read_bytes()
    content_type = guess_content_type(path)

    response_headers = _prepare_headers(content_type, headers)

    if as_attachment:
        filename = download_name or path.name
        safe_filename = Path(filename).name.replace('"', '_').replace("\r", '_').replace("\n", '_')

        response_headers["Content-Disposition"] = f"attachment; filename=\"{safe_filename}\""

    return body, status_code, response_headers

def redirect_response(location, status_code=302, headers=None):
    if status_code not in REDIRECT_STATUS_CODES:
        raise ValueError(f"Invalid redirect status code: {status_code}")

    response_headers = _prepare_headers(headers=headers)
    response_headers["Location"] = location
    return "", status_code, response_headers

def empty_response(status_code=204, headers=None):
    response_headers = _prepare_headers(headers=headers)
    return b"", status_code, response_headers

def set_cookie(
        response,
        key,
        value,
        max_age=None,
        expires=None,
        path="/",
        domain=None,
        secure=False,
        http_only=False,
        same_site=None
):

    body, status_code, headers = response

    if headers is None:
        response_headers = []
    elif isinstance(headers, dict):
        response_headers = list(headers.items())
    else:
        response_headers = list(headers)

    cookie = SimpleCookie()
    cookie[key] = value

    morsel = cookie[key]
    if max_age is not None:
        morsel["max-age"] = str(max_age)
    if expires is not None:
        morsel["expires"] = expires
    if path is not None:
        morsel["path"] = path
    if domain is not None:
        morsel["domain"] = domain
    if secure:
        morsel["secure"] = True
    if http_only:
        morsel["httpOnly"] = True
    if same_site is not None:
        morsel["samesite"] = same_site

    response_headers.append(("Set-Cookie", morsel.OutputString()))

    return body, status_code, response_headers

def delete_cookie(response, key, path="/", domain=None):
    return set_cookie(
        response=response,
        key=key,
        value="",
        max_age=0,
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
        path=path,
        domain=domain
    )
        
def test_delete_cookie_expires_cookie():
    response = text_response("Logged out")

    body, status_code, headers = (
        delete_cookie(
            response=response,
            key="session_id",
            path="/",
        )
    )

    cookie_header = next(
        value
        for name, value in headers
        if name.lower() == "set-cookie"
    )

    cookie = SimpleCookie()
    cookie.load(cookie_header)

    morsel = cookie["session_id"]

    assert morsel.value == ""
    assert morsel["max-age"] == "0"
    assert morsel["expires"] == (
        "Thu, 01 Jan 1970 00:00:00 GMT"
    )
    assert morsel["path"] == "/"

