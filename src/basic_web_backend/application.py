from html import escape
from traceback import format_exc

from .config import ApplicationConfig
from .exceptions import HTTPException
from .response import html_response
from .routing import Router


class WebApplication:
    def __init__(self, config=None):
        if config is None:
            config = ApplicationConfig()

        self.config = config
        self.router = Router()
        self.error_handlers = {}

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