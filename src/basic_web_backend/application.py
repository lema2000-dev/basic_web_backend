from .config import ApplicationConfig
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
        request = self.config.request_adapter.convert(
            server_request
        )

        route_match = self.router.match_route(path=request.path, method=request.method)

        response = route_match.view(request=request, **route_match.parameters)

        return self.config.response_adapter.convert(response)

        