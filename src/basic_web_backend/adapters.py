from .request import Request

class LemaRequestAdapter:
    def convert(self, server_request):
        method = server_request.method
        path = server_request.path
        query_string = server_request.query_string
        headers = server_request.headers
        body = server_request.body

        return Request(method, path, query_string, headers, body)

class LemaResponseAdapter:
    def convert(self, backend_response):
        if not isinstance(backend_response, tuple):
            return backend_response
        if len(backend_response) != 3:
            return backend_response

        body, status_code, headers = backend_response

        filtered_headers = self._remove_content_length(headers)

        return body, status_code, filtered_headers

    def _remove_content_length(self, headers):
        if headers is None:
            return None

        if isinstance(headers, dict):
            return {
                name: value for name, value in headers.items()
                if name.lower() != "content-length"
            }

        return [
            (name, value) for name, value in headers
            if name.lower() != "content-length"
        ]