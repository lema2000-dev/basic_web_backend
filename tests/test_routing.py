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
    match = router.match_route(path="/", method="GET")

    assert isinstance(match, RouteMatch)
    assert match.view is example_view
    assert match.parameters == {}

def test_router_normalizes_method_names():
    router = Router()
    router.add_route(path="/users", view=example_view, methods=["get", "post"])

    get_match = router.match_route(path="/users", method="GET")
    post_match = router.match_route(path="/users", method="POST")

    assert get_match.view is example_view
    assert post_match.view is example_view

def test_router_uses_get_as_default_method():
    router = Router()
    router.add_route(path="/default", view=example_view)

    match = router.match_route(path="/default", method="GET")

    assert match.view is example_view

def test_router_accepts_different_methods_for_same_path():
    def get_users_view():
        return "GET Users"

    def post_users_view():
        return "POST Users"

    router = Router()
    router.add_route(path="/users", view=get_users_view, methods=["GET"])
    router.add_route(path="/users", view=post_users_view, methods=["POST"])

    get_match = router.match_route(path="/users", method="GET")
    post_match = router.match_route(path="/users", method="POST")

    assert get_match.view is get_users_view
    assert post_match.view is post_users_view

def test_router_rejects_duplicate_route():
    router = create_router_with_index_route()

    with pytest.raises(DuplicateRouteError):
        router.add_route(path="/", view=example_view, methods=["GET"])

def test_router_raises_not_found_for_unkown_path():
    router = create_router_with_index_route()

    with pytest.raises(NotFound) as exc_info:
        router.match_route(path="/unknown", method="GET")

    assert exc_info.value.path == "/unknown"

def test_router_raises_method_not_allowed():
    router = Router()
    router.add_route(path="/users", view=example_view, methods=["GET", "HEAD"])

    with pytest.raises(MethodNotAllowed) as exc_info:
        router.match_route(path="/users", method="POST")

    error = exc_info.value
    assert error.method == "POST"
    assert error.path == "/users"
    assert error.allowed_methods == ("GET", "HEAD")

def test_router_treats_trailing_slash_as_different_path():
    router = Router()
    router.add_route(path="/about", view=example_view, methods=["GET"])

    with pytest.raises(NotFound) as exc_info:
        router.match_route(path="/about/", method="GET")

def test_router_matches_string_parameter():
    router = Router()

    router.add_route(path="/users/<string:username>", view=example_view, methods=["GET"])

    match = router.match_route(path="/users/johndoe", method="GET")

    assert match.view is example_view
    assert match.parameters == {"username": "johndoe"}

def test_router_matches_int_parameter():
    router = Router()

    router.add_route(path="/items/<int:item_id>", view=example_view, methods=["GET"])

    match = router.match_route(path="/items/42", method="GET")

    assert match.view is example_view
    assert match.parameters == {"item_id": 42}

def test_int_parameter_rejects_non_integer():
    router = Router()

    router.add_route(path="/items/<int:item_id>", view=example_view, methods=["GET"])

    with pytest.raises(NotFound):
        router.match_route(path="/items/notanumber", method="GET")

def test_router_matches_float_parameter():
    router = Router()

    router.add_route(path="/measurements/<float:value>", view=example_view, methods=["GET"])

    match = router.match_route(path="/measurements/3.14", method="GET")

    assert match.view is example_view
    assert match.parameters == {"value": 3.14}

def test_router_matches_path_parameter():
    router = Router()

    router.add_route(path="/files/<path:file_path>", view=example_view, methods=["GET"])

    match = router.match_route(path="/files/some/nested/path.txt", method="GET")

    assert match.view is example_view
    assert match.parameters == {"file_path": "some/nested/path.txt"}

def test_router_matches_multiple_parameters():
    router = Router()

    router.add_route(path="/users/<string:username>/posts/<int:post_id>", view=example_view, methods=["GET"])

    match = router.match_route(path="/users/johndoe/posts/42", method="GET")

    assert match.view is example_view
    assert match.parameters == {"username": "johndoe", "post_id": 42}

def test_static_route_has_priority_over_dynamic_route():
    router = Router()

    def new_user(request):
        return "New User"

    def user_profile(request, username):
        return f"Profile of {username}"

    router.add_route(path="/users/new", view=new_user, methods=["GET"])
    router.add_route(path="/users/<string:username>", view=user_profile, methods=["GET"])

    match = router.match_route(path="/users/new", method="GET")
    assert match.view is new_user
    assert match.parameters == {}

    match_dynamic = router.match_route(path="/users/johndoe", method="GET")
    assert match_dynamic.view is user_profile
    assert match_dynamic.parameters == {"username": "johndoe"}

def test_dynamic_route_raises_method_not_allowed():
    router = Router()

    router.add_route(path="/users/<string:username>", view=example_view, methods=["GET", "HEAD"])

    with pytest.raises(MethodNotAllowed) as exc_info:
        router.match_route(path="/users/johndoe", method="POST")

    error = exc_info.value

    assert error.method == "POST"
    assert error.path == "/users/johndoe"
    assert error.allowed_methods == ("GET", "HEAD")

    