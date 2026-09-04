from html import escape
from traceback import format_exc

from .config import ApplicationConfig
from .exceptions import BadRequest, HTTPException, PayloadTooLarge
from .response import html_response
from .routing import Router
from .static import StaticFileHandler


class WebApplication:
    def __init__(self, config=None):
        if config is None:
            config = ApplicationConfig()

        self.config = config
        self.router = Router()
        self.error_handlers = {}
        self.static_handler = None

        if self.config.static_folder is not None:
            self._register_static_route()

    def _register_static_route(self):
        static_url_path = ("/" + self.config.static_url_path.strip("/"))

        if static_url_path == "/":
            route_path = "/<path:filename>"
        else:
            route_path = f"{static_url_path}/<path:filename>"

        self.static_handler = StaticFileHandler(static_folder=self.config.static_folder)
        self.router.add_route(path=route_path, view=self._serve_static_file, methods=["GET"])

    def _serve_static_file(self, request, filename):
        return self.static_handler.serve(filename=filename)

    def route(self, path, methods=None):
        def decorator(view):
            self.router.add_route(path=path, view=view, methods=methods)
            return view
        return decorator

    def errorhandler(self, status_code):
        def decorator(handler):
            self.error_handlers[status_code] = handler
            return handler
        return decorator

    def __call__(self, server_request):

        try:
            request = self.config.request_adapter.convert(
                server_request
            )

            self._check_content_length(request)

            route_match = self.router.match_route(path=request.path, method=request.method)

            response = route_match.view(request=request, **route_match.parameters)

        except HTTPException as error:
            response = self._handle_http_exception(error)


        except Exception as error:
            response = self._handle_internal_error(error)

        return self.config.response_adapter.convert(response)

    def _handle_http_exception(self, error):
        handler = self.error_handlers.get(error.status_code)

        if handler is not None:
            return handler(error)

        title = f"{error.status_code} {error.default_message}"

        body = f"<h1>{escape(title)}</h1>"

        if error.message != error.default_message:
            body += f"<p>{escape(error.message)}</p>"

        return html_response(
            body=body,
            status_code=error.status_code,
            headers=error.headers
        )

    def _handle_internal_error(self, error):
        handler = self.error_handlers.get(500)

        if handler is not None:
            return handler(error)

        if self.config.debug:
            error_type = type(error).__name__
            error_message = escape(str(error))
            error_traceback = escape(format_exc())

            return html_response(
                body=(
                    f"<h1>500 Internal Server Error</h1>"
                    f"<h2>{error_type}: {error_message}</h2>"
                    f"<pre>{error_traceback}</pre>"
                ),
                status_code=500
            )

        return html_response(
            body="<h1>500 Internal Server Error</h1>",
            status_code=500
        )

    def _check_content_length(self, request):
        limit = self.config.max_content_length

        if limit is None:
            return

        body = request.body

        if isinstance(body, str):
            body_length = len(body.encode("utf-8"))
        else:
            body_length = len(body)

        if body_length > limit:
            raise PayloadTooLarge(f"The request body exceeds the {limit}-byte limit.")
