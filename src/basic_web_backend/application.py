from .config import ApplicationConfig
from .exceptions import MethodNotAllowed, NotFound
from .response import html_response
from .routing import Router
from html import escape
from traceback import format_exc

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

        except NotFound as error:
            handler = self.error_handlers.get(404)
            if handler is None:
                response = html_response(
                    "<h1>404 Not Found</h1>",
                    status_code=404
                )
            else:
                response = handler(error)
            
        except MethodNotAllowed as error:
            handler = self.error_handlers.get(405)
            if handler is None:
                allowed_methods = ", ".join(sorted(error.allowed_methods))

                response = html_response(
                    f"<h1>405 Method Not Allowed</h1>",
                    status_code=405,
                    headers={
                        "Allow": allowed_methods
                    }
                )
            else:
                response = handler(error)

        except Exception as error:
            handler = self.error_handlers.get(500)
            if handler is not None:
                response = handler(error)
            elif self.config.debug:
                error_type = type(error).__name__
                error_message = escape(str(error))
                traceback_text = format_exc()
                response = html_response(
                    "<h1>500 Internal Server Error</h1>"
                    f"<p><strong>{error_type}:</strong>: "
                    f"{error_message}</p>"
                    f"<pre>{escape(traceback_text)}</pre>",
                    status_code=500
                )
            else:
                response = html_response(
                    "<h1>500 Internal Server Error</h1>",
                    status_code=500
                )

        return self.config.response_adapter.convert(response)

    