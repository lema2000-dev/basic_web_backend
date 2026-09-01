import pytest

from basic_web_backend.exceptions import (
    DuplicateRouteError,
    MethodNotAllowed,
    NotFound,
)
from basic_web_backend.routing import Router, RouteMatch

def example_view():
    return "Hello, World!"

def create_router_with_index_route():
    router = Router()
    router.add_route(path="/", view=example_view, methods=["GET"])
    return router

def test_router_registers_exact_route():
    router = create_router_with_index_route()
    match = router.match(path="/", method="GET")

    assert isinstance(match, RouteMatch)
    assert match.view is example_view
    assert match.parameters == {}

def test_router_normalizes_method_names():
    router = Router()
    router.add_route(path="/users", view=example_view, methods=["get", "post"])

    get_match = router.match(path="/users", method="GET")
    post_match = router.match(path="/users", method="POST")

    assert get_match.view is example_view
    assert post_match.view is example_view

def test_router_uses_get_as_default_method():
    router = Router()
    router.add_route(path="/default", view=example_view)

    match = router.match(path="/default", method="GET")

    assert match.view is example_view

def test_router_accepts_different_methods_for_same_path():
    def get_users_view():
        return "GET Users"

    def post_users_view():
        return "POST Users"

    router = Router()
    router.add_route(path="/users", view=get_users_view, methods=["GET"])
    router.add_route(path="/users", view=post_users_view, methods=["POST"])

    get_match = router.match(path="/users", method="GET")
    post_match = router.match(path="/users", method="POST")

    assert get_match.view is get_users_view
    assert post_match.view is post_users_view

def test_router_rejects_duplicate_route():
    router = create_router_with_index_route()

    with pytest.raises(DuplicateRouteError):
        router.add_route(path="/", view=example_view, methods=["GET"])

def test_router_raises_not_found_for_unkown_path():
    router = create_router_with_index_route()

    with pytest.raises(NotFound) as exc_info:
        router.match(path="/unknown", method="GET")

    assert exc_info.value.path == "/unknown"

def test_router_raises_method_not_allowed():
    router = Router()
    router.add_route(path="/users", view=example_view, methods=["GET", "HEAD"])

    with pytest.raises(MethodNotAllowed) as exc_info:
        router.match(path="/users", method="POST")

    error = exc_info.value
    assert error.method == "POST"
    assert error.path == "/users"
    assert error.allowed_methods == ("GET", "HEAD")

def test_router_treats_trailing_slash_as_different_path():
    router = Router()
    router.add_route(path="/about", view=example_view, methods=["GET"])

    with pytest.raises(NotFound) as exc_info:
        router.match(path="/about/", method="GET")