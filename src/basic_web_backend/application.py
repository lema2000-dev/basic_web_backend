from .config import ApplicationConfig
from .exceptions import MethodNotAllowed, NotFound
from .response import html_response
from .routing import Router

class WebApplication:
    def __init__(self, config=None):
        if config is None:
            config = ApplicationConfig()

        self.config = config
        self.router = Router()

    def route(self, path, methods=None):
        def decorator(view):
            self.router.add_route(path=path, view=view, methods=methods)
            return view
        return decorator

    def __call__(self, server_request):

        try:
            request = self.config.request_adapter.convert(
                server_request
            )

            route_match = self.router.match_route(path=request.path, method=request.method)

            response = route_match.view(request=request, **route_match.parameters)

        except NotFound:
            response = html_response(
                "<h1>404 Not Found</h1>",
                status_code=404
            )
        except MethodNotAllowed as error:
            allowed_methods = ", ".join(sorted(error.allowed_methods))

            response = html_response(
                f"<h1>405 Method Not Allowed</h1>",
                status_code=405,
                headers={
                    "Allow": allowed_methods
                }
            )

        except Exception:
            response = html_response(
                "<h1>500 Internal Server Error</h1>",
                status_code=500
            )

        return self.config.response_adapter.convert(response)

    