import re
from dataclasses import dataclass
from collections.abc import Callable

from .exceptions import (
    AmbiguousRouteError,
    DuplicateRouteError,
    InvalidRouteError,
    MethodNotAllowed,
    NotFound
)

PARAMETER_PATTERN = re.compile(r"<(?P<converter>string|int|float|path):"
    r"(?P<name>[a-zA-Z_]\w*)>")

CONVERTERS = {
    "string": (r"[^/]+", str),
    "int": (r"\d+", int),
    "float": (r"(?:\d+(?:\.\d*)?)|\.\d+", float),
    "path": (r".+", str),
}

CONVERTER_OVERLAPS = {
    "string": {"string", "int", "float", "path"},
    "int": {"string", "int", "float", "path"},
    "float": {"string", "int", "float", "path"},
    "path": {"string", "int", "float", "path"},
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
    segments: list
    methods: dict

class Router:
    def __init__(self):
        self.static_routes = {}
        self.dynamic_routes = []

    def add_route(self, path, view, methods=None):
        methods = self._prepare_methods(methods)

        if PARAMETER_PATTERN.search(path):
            self._add_dynamic_route(path=path, methods=methods, view=view)
        else:
            self._add_static_route(path=path, methods=methods, view=view)

    def _prepare_methods(self, methods):
        if methods is None:
            return ["GET"]

        normalized_methods = {method.upper()for method in methods}
        return normalized_methods

    def _add_static_route(self, path, view, methods):
        registered_methods = self.static_routes.setdefault(path, {})

        for method in methods:
            if method in registered_methods:
                raise DuplicateRouteError(path=path, method=method)

        for method in methods:
            registered_methods[method] = view

    def _add_dynamic_route(self, path, view, methods):
        existing_same_route = self._find_dynamic_route(path)

        if existing_same_route is not None:
            duplicate_methods = methods & existing_same_route.methods.keys()
            if duplicate_methods:
                duplicate_method = sorted(duplicate_methods)[0]

                raise DuplicateRouteError(path=path, method=duplicate_method)

            for method in methods:
                existing_same_route.methods[method] = view

            return
        new_route = self._compile_dynamic_route(path)

        self._check_dynamic_ambiguity(new_route=new_route, methods=methods)

        new_route.methods = {method: view for method in methods}

        self.dynamic_routes.append(new_route)

    def _find_dynamic_route(self, path):
        for dynamic_route in self.dynamic_routes:
            if dynamic_route.path_pattern == path:
                return dynamic_route

        return None

    def _compile_dynamic_route(self, path):
        if not path.startswith("/"):
            raise InvalidRouteError(path=path, message="The route must start with '/'.")

        raw_segments = path[1:].split("/")
        segments = []
        regex_parts = []
        converters = {}

        for index, raw_segment in enumerate(raw_segments):
            paramater_match = PARAMETER_PATTERN.fullmatch(raw_segment)
            if paramater_match is None:
                if "<" in raw_segment or ">" in raw_segment:
                    raise InvalidRouteError(
                        path=path,
                        message="A parameter must be in the format <converter:name>."
                    )
                segments.append(("static", raw_segment))
                regex_parts.append(re.escape(raw_segment))
                continue

            converter_name = paramater_match.group("converter")
            parameter_name = paramater_match.group("name")

            if parameter_name in converters:
                raise InvalidRouteError(
                    path=path,
                    message=f"Duplicate parameter name: {parameter_name!r}."

                )

            if converter_name == "path" and index != len(raw_segments) - 1:
                raise InvalidRouteError(
                    path=path,
                    message="The 'path' converter must be the final route segment."
                )

            converter_pattern, converter = CONVERTERS[converter_name]
            segments.append(("dynamic", converter_name))
            regex_parts.append(f"(?P<{parameter_name}>{converter_pattern})")
            converters[parameter_name] = converter

        regex_source = "^/" + "/".join(regex_parts) + "$"

        return DynamicRoute(
            path_pattern=path,
            regex=re.compile(regex_source),
            converters=converters,
            segments=segments,
            methods={}
        )

    def _check_dynamic_ambiguity(self, new_route, methods):
        for existing_route in self.dynamic_routes:
            common_methods = methods & existing_route.methods.keys()

            if not common_methods:
                continue

            if self._routes_overlap(new_route.segments, existing_route.segments):
                raise AmbiguousRouteError(
                    path=new_route.path_pattern,
                    conflicting_path=existing_route.path_pattern,
                    methods=common_methods
                )

    def _routes_overlap(self, first_segments, second_segments):
        if len(first_segments) == len(second_segments):
            return self._prefixes_overlap(first_segments, second_segments)

        if len(first_segments) < len(second_segments):
            shorter = first_segments
            longer = second_segments
        else:
            shorter = second_segments
            longer = first_segments

        if not self._ends_with_path(shorter):
            return False

        shorter_prefix = shorter[:-1]
        longer_prefix = longer[:len(shorter_prefix)]
        return self._prefixes_overlap(shorter_prefix, longer_prefix)

    def _ends_with_path(self, segments):
        if not segments:
            return False

        return segments[-1] == ("dynamic", "path")

    def _prefixes_overlap(self, first_segments, second_segments):
        for first_segment, second_segment in zip(first_segments, second_segments):
            if not self._segments_overlap(first_segment, second_segment):
                return False

        return True

    def _segments_overlap(self, first_segment, second_segment):
        first_kind, first_value = first_segment
        second_kind, second_value = second_segment

        if first_kind == "static" and second_kind == "static":
            return first_value == second_value

        if first_kind == "static" and second_kind == "dynamic":
            return self._static_matches_converter(first_value, second_value)

        if first_kind == "dynamic" and second_kind == "static":
            return self._static_matches_converter(second_value, first_value)

        return (
            second_value
            in CONVERTER_OVERLAPS[first_value]
        )

    def _static_matches_converter(self, value, converter_name):
        converter_pattern, _ = CONVERTERS[converter_name]

        return (re.fullmatch(converter_pattern, value) is not None)

    def match_route(self, path, method):
        normalized_method = method.upper()

        registered_methods = self.static_routes.get(path)

        if registered_methods is not None:
            view = registered_methods.get(normalized_method)

            if view is None:
                raise MethodNotAllowed(
                    method=normalized_method,
                    path=path,
                    allowed_methods=registered_methods.keys()
                )

            return RouteMatch(view=view, parameters={})

        return self._match_dynamic_route(path=path, method=normalized_method)

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

            parameters = self._convert_parameters(
                regex_match=regex_match,
                converters=dynamic_route.converters
            )

            return RouteMatch(view=view, parameters=parameters)

        if allowed_methods:
            raise MethodNotAllowed(
                method=method,
                path=path,
                allowed_methods=allowed_methods
            )

        raise NotFound(path=path)

    def _convert_parameters(self, regex_match, converters):
        parameters = {}

        for name, value in regex_match.groupdict().items():
            converter = converters[name]
            parameters[name] = converter(value)

        return parameters

        
