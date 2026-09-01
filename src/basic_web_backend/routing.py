from dataclasses import dataclass
from collections.abc import Callable

from .exceptions import DuplicateRouteError, MethodNotAllowed, NotFound

@dataclass
class RouteMatch:
    view: Callable
    parameters: dict

class Router:
    def __init__(self):
        self.routes = {}

    def add_route(self, path, view, methods=None):
        if methods is None:
            methods = ["GET"]

        normalized_methods = {method.upper() for method in methods}
        registered_methods = self.routes.get(path, {}).keys()
        duplicate_methods = normalized_methods & registered_methods

        if duplicate_methods:
            formatted_methods = ", ".join(sorted(duplicate_methods))
            raise DuplicateRouteError(
                f"Route '{path}' is already registered for methods: {formatted_methods}"
            )

        if path not in self.routes:
            self.routes[path] = {}

        for method in normalized_methods:
            self.routes[path][method] = view

    def match(self, path, method):
        registered_methods = self.routes.get(path)
        if registered_methods is None:
            raise NotFound(path)

        normalized_method = method.upper()
        view = registered_methods.get(normalized_method)

        if view is None:
            raise MethodNotAllowed(normalized_method, path, registered_methods.keys())

        return RouteMatch(view=view, parameters={})