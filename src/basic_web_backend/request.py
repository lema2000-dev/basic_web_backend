import json
from urllib.parse import parse_qs
from http.cookies import CookieError, SimpleCookie

from .exceptions import BadRequest, UnsupportedMediaType

class Request:
    def __init__(self, method, path, query_string="", headers=None, body=b""):
        if not isinstance(body, (str, bytes)):
            raise BadRequest("The request body must be bytes or text")

        self.method = method.upper()
        self.path = path
        self.query_string = query_string
        self.body = body

        if headers is None:
            header_items = []
        elif isinstance(headers, dict):
            header_items = headers.items()
        else:
            header_items = headers

        self.headers = [(k.lower(), v) for k, v in header_items]
        self.query = parse_qs(query_string, keep_blank_values=True)

    def get_header(self, name, default=None):
        normalized_name = name.lower()

        for header_name, header_value in self.headers:
            if header_name == normalized_name:
                return header_value

        return default

    def get_headers(self, name):
        normalized_name = name.lower()
        return [value for header_name, value in self.headers if header_name == normalized_name]

    @property
    def content_type(self):
        conetnt_type, parameters = self._parse_content_type()
        return conetnt_type

    @property
    def charset(self):
        content_type, parameters = self._parse_content_type()

        charset = parameters.get("charset")
        if charset is None:
            return None

        return charset.lower()

    def _parse_content_type(self):
        header_value = self.get_header("content-type")

        if header_value is None:
            return None, {}

        parts = header_value.split(";")
        content_type = parts[0].strip().lower()

        if not content_type:
            content_type = None

        parameters = {}

        for part in parts[1:]:
            name, sep, value = part.partition("=")
            if not sep:
                continue

            name = name.strip().lower()
            value = value.strip()

            if (
                len(value) >= 2 and value[0] == '"' and value[-1] == '"'
            ):
                value = value[1:-1]

            if name:
                parameters[name] = value

        return content_type, parameters

    def get_json(self):
        content_type = self.content_type

        is_json = (content_type == "application/json" or (content_type is not None and content_type.endswith("+json")))

        if not is_json:
            raise UnsupportedMediaType("The request content type must be JSON")

        charset = self.charset or "utf-8"

        try:
            if isinstance(self.body, bytes):
                body_text = self.body.decode(charset)
            else:
                body_text = self.body

        except LookupError:
            raise BadRequest(f"The charset '{charset}' is not supported")
        except UnicodeDecodeError:
            raise BadRequest(f"The request body could not be decoded using the charset '{charset}'")

        try:
            return json.loads(body_text)
        except json.JSONDecodeError:
            raise BadRequest("The request body is not valid JSON")

    def get_form(self):
        if self.content_type != "application/x-www-form-urlencoded":
            raise UnsupportedMediaType("The request content type must be application/x-www-form-urlencoded")

        charset = self.charset or "utf-8"

        try:
            if isinstance(self.body, bytes):
                body_text = self.body.decode(charset)
            else:
                body_text = self.body

            return parse_qs(body_text, keep_blank_values=True, encoding=charset, errors="strict")

        except LookupError:
            raise BadRequest(f"Unsupported character encoding: '{charset}'")
        except UnicodeDecodeError:
            raise BadRequest(f"The request body could not be decoded using the charset '{charset}'")

    @property
    def cookies(self):
        cookie_headers = self.get_headers("cookie")

        if cookie_headers is None:
            return {}

        result = {}

        for header_value in cookie_headers:
            cookie = SimpleCookie()
            try:
                cookie.load(header_value)
            except CookieError:
                raise BadRequest("The request contains invalid cookie header.")

            for name, morsel in cookie.items():
                result[name] = morsel.value

        return result

    