import json
from urllib.parse import parse_qs

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
