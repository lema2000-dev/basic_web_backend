import re
from dataclasses import dataclass
from collections.abc import Callable

from .exceptions import DuplicateRouteError, MethodNotAllowed, NotFound

PARAMETER_PATTERN = re.compile(r"<(?P<converter>string|int|float|path):"
    r"(?P<name>[a-zA-Z_]\w*)>")

CONVERTERS = {
    "string": (r"[^/]+", str),
    "int": (r"\d+", int),
    "float": (r"(?:\d+(?:\.\d*)?)|\.\d+", float),
    "path": (r".+", str),
}

@dataclass
class RouteMatch:
    view: Callable
    parameters: dict

@dataclass
class DynamicRoute:
    path_pattern: str
    regex: re.Pattern
    converters: dict
    methods: dict

class Router:
    def __init__(self):
        self.static_routes = {}
        self.dynamic_routes = []

    def add_route(self, path, view, methods=None):
        if methods is None:
            methods = ["GET"]

        normalized_methods = {method.upper(): view for method in methods}

        if PARAMETER_PATTERN.search(path):
            self._add_dynamic_route(path=path, methods=normalized_methods, view=view)
        else:
            self._add_static_route(path=path, methods=normalized_methods, view=view)

    def match_route(self, path, method):
        normalized_method = method.upper()
        static_match = self._match_static_route(path=path, method=normalized_method)

        if static_match is not None:
            return static_match

        return self._match_dynamic_route(path=path, method=normalized_method)
    
    def _add_static_route(self, path, methods, view):
        registered_methods = self.static_routes.get(path, {})

        self._chechk_duplicate_methods(path=path, new_methods=methods, registered_methods=registered_methods)

        if path not in self.static_routes:
            self.static_routes[path] = {}

        for method in methods:
            self.static_routes[path][method] = view

    def _add_dynamic_route(self, path, methods, view):
        dynamic_route = self._find_dynamic_route(path)

        if dynamic_route is None:
            regex, converters = self._compile_path(path)
            dynamic_route = DynamicRoute(
                path_pattern=path,
                regex=regex,
                converters=converters,
                methods={}
            )
            self.dynamic_routes.append(dynamic_route)

        self._chechk_duplicate_methods(path=path, new_methods=methods, registered_methods=dynamic_route.methods)

        for method in methods:
            dynamic_route.methods[method] = view

    def _chechk_duplicate_methods(self, path, new_methods, registered_methods):
        duplicate_methods = new_methods & registered_methods.keys()

        if not duplicate_methods:
            return

        formatted_methods = ", ".join(sorted(duplicate_methods))
        raise DuplicateRouteError(
            f"Route '{path}' is already registered for the following methods: {formatted_methods}"
        )

    def _find_dynamic_route(self, path):
        for dynamic_route in self.dynamic_routes:
            if dynamic_route.path_pattern == path:
                return dynamic_route

        return None

    def _compile_path(self, path):
        regex_parts = ["^"]
        converters = {}

        current_position = 0

        for parameter_match in PARAMETER_PATTERN.finditer(path):
            static_part = path[current_position:parameter_match.start()]
            regex_parts.append(re.escape(static_part))

            converter_name = parameter_match.group("converter")
            parameter_name = parameter_match.group("name")

            parameter_regex, converter = CONVERTERS[converter_name]
            regex_parts.append(f"(?P<{parameter_name}>{parameter_regex})")

            converters[parameter_name] = converter
            current_position = parameter_match.end()

        remaining_part = path[current_position:]
        regex_parts.append(re.escape(remaining_part))
        regex_parts.append("$")

        compiled_regex = re.compile("".join(regex_parts))

        return compiled_regex, converters

    def _match_static_route(self, path, method):
        registered_methods = self.static_routes.get(path)

        if registered_methods is None:
            return None

        view = registered_methods.get(method)

        if view is None:
            raise MethodNotAllowed(method=method, path=path, allowed_methods=registered_methods.keys())

        return RouteMatch(view=view, parameters={})

    def _match_dynamic_route(self, path, method):
        allowed_methods = set()

        for dynamic_route in self.dynamic_routes:
            regex_match = dynamic_route.regex.fullmatch(path)

            if regex_match is None:
                continue

            allowed_methods.update(dynamic_route.methods.keys())

            view = dynamic_route.methods.get(method)

            if view is None:
                continue

            parameters = self._convert_parameters(regex_match=regex_match, converters=dynamic_route.converters)

            return RouteMatch(view=view, parameters=parameters)

        if allowed_methods:
            raise MethodNotAllowed(method=method, path=path, allowed_methods=allowed_methods)

        raise NotFound(path=path)

    def _convert_parameters(self, regex_match, converters):
        parameters = {}

        for name, value in regex_match.groupdict().items():
            converter = converters[name]
            parameters[name] = converter(value)

        return parameters
        
