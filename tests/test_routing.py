import pytest

from basic_web_backend.exceptions import (
    DuplicateRouteError,
    InvalidRouteError,
    MethodNotAllowed,
    NotFound,
    AmbiguousRouteError
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

def test_add_route_rejects_ambiguous_dynamic_routes():
    router = Router()

    def find_by_name(request, name):
        return name

    def find_by_id(request, id):
        return id

    router.add_route(
        path="/search/<string:name>",
        view=find_by_name,
        methods=["GET"]
    )

    with pytest.raises(AmbiguousRouteError):
        router.add_route(
            path="/search/<int:id>",
            view=find_by_id,
            methods=["GET"]
        )

def test_dynamic_routes_with_different_methods_are_not_ambiguous():
    router = Router()

    def read_item(request, item_name):
        return item_name

    def update_item(request, item_id):
        return item_id

    router.add_route(
        path="/items/<string:item_name>",
        view=read_item,
        methods=["GET"]
    )

    router.add_route(
        path="/items/<int:item_id>",
        view=update_item,
        methods=["POST"]
    )

    get_route_match = router.match_route(path="/items/widget", method="GET")

    assert get_route_match.view is read_item
    assert get_route_match.parameters == {"item_name": "widget"}

    post_route_match = router.match_route(path="/items/42", method="POST")

    assert post_route_match.view is update_item
    assert post_route_match.parameters == {"item_id": 42}


def test_add_route_rejects_non_final_path_converter():
    router = Router()

    def download(request, filename):
        return filename

    with pytest.raises(InvalidRouteError):
        router.add_route(
            path="/files/<path:filename>/download",
            view=download,
            methods=["GET"],
        )

def test_add_route_accepts_final_path_converter():
    router = Router()

    def serve_file(request, filename):
        return filename

    router.add_route(
        path="/files/<path:filename>",
        view=serve_file,
        methods=["GET"],
    )

    route_match = router.match_route(
        path="/files/images/logo.png",
        method="GET",
    )

    assert route_match.view is serve_file
    assert route_match.parameters == {
        "filename": "images/logo.png",
    }

def test_add_route_rejects_ambiguity_created_by_path_converter():
    router = Router()

    def serve_file(request, filename):
        return filename

    def serve_image(request, image_name):
        return image_name

    router.add_route(
        path="/files/<path:filename>",
        view=serve_file,
        methods=["GET"],
    )

    with pytest.raises(AmbiguousRouteError):
        router.add_route(
            path="/files/images/<string:image_name>",
            view=serve_image,
            methods=["GET"],
        )

def test_add_route_allows_non_overlapping_dynamic_routes():
    router = Router()

    def find_user(request, value):
        return value

    def find_product(request, value):
        return value

    router.add_route(
        path="/users/<string:value>",
        view=find_user,
        methods=["GET"],
    )

    router.add_route(
        path="/products/<int:value>",
        view=find_product,
        methods=["GET"],
    )

    user_match = router.match_route(
        path="/users/alice",
        method="GET",
    )
    product_match = router.match_route(
        path="/products/42",
        method="GET",
    )

    assert user_match.view is find_user
    assert product_match.view is find_product

def test_ambiguous_route_is_not_registered():
    router = Router()

    def find_by_name(request, name):
        return name

    def find_by_id(request, item_id):
        return item_id

    router.add_route(
        path="/search/<string:name>",
        view=find_by_name,
        methods=["GET"],
    )

    with pytest.raises(AmbiguousRouteError):
        router.add_route(
            path="/search/<int:item_id>",
            view=find_by_id,
            methods=["GET"],
        )

    route_match = router.match_route(
        path="/search/42",
        method="GET",
    )

    assert route_match.view is find_by_name
    assert route_match.parameters == {
        "name": "42",
    }