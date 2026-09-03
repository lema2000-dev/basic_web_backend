from basic_web_backend.application import WebApplication
from basic_web_backend.config import ApplicationConfig
from basic_web_backend.request import Request
from basic_web_backend.exceptions import (
    MethodNotAllowed,
    NotFound,
)
import basic_web_backend.response as ResponseModule

class FakeRequestAdapter:
    def __init__(self):
        self.received_server_request = None

    def convert(self, server_request):
        self.received_server_request = server_request
        return Request(
            method=server_request["method"],
            path=server_request["path"]
        )

class FakeResponseAdapter:
    def __init__(self):
        self.received_response = None

    def convert(self, response):
        self.received_response = response
        return {"converted" : response}

def create_application():
    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()
    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter
    )

    app = WebApplication(config=config)

    return app, request_adapter, response_adapter  

def test_route_decorator_returns_original_view():
    app, _, _ = create_application()

    def index_view(request):
        return "Hello, World!"

    decorated_view = app.route(path="/")(index_view)

    assert decorated_view is index_view

def test_route_decorator_registers_view():
    app, _, _ = create_application()

    @app.route("/")
    def index_view(request):
        return "Hello, World!"

    route_match = app.router.match_route(path="/", method="GET")
    assert route_match.view is index_view
    assert route_match.parameters == {}

def test_route_accepts_methods_argument():
    app, _, _ = create_application()

    @app.route("/users", methods=["GET", "POST"])
    def users_view(request):
        return "Users"

    get_match = app.router.match_route(path="/users", method="GET")
    post_match = app.router.match_route(path="/users", method="POST")

    assert get_match.view is users_view
    assert post_match.view is users_view

def test_application_adapts_request_and_response():
    app, request_adapter, response_adapter = create_application()

    @app.route("/test")
    def test_view(request):
        return "Test Response"

    server_request = {"method": "GET", "path": "/test"}
    result = app(server_request)

    assert request_adapter.received_server_request is server_request
    assert response_adapter.received_response == "Test Response"
    assert result == {"converted": "Test Response"}

def test_application_passes_dynamic_parameters_to_view():
    app, _, response_adapter = create_application()

    @app.route("/users/<string:username>")
    def user_profile(request, username):
        return f"Profile of {username}"

    server_request = {"method": "GET", "path": "/users/johndoe"}
    result = app(server_request)

    assert result == {"converted": "Profile of johndoe"}
    assert response_adapter.received_response == "Profile of johndoe"

def test_application_returns_404_for_unknown_path():
    app, _, response_adapter = create_application()

    result = app({"method": "GET", "path": "/unknown"})

    body, status_code, headers = response_adapter.received_response

    assert status_code == 404
    assert "404" in body
    assert "Not Found" in body
    assert headers == {
        "Content-Type": "text/html; charset=utf-8"
    }
    assert result == {"converted": (body, status_code, headers)}

def test_application_returns_405_for_unsupported_method():
    app, _, response_adapter = create_application()

    @app.route("/users", methods=["GET"])
    def users(request):
        return "Users"

    app({"method": "POST", "path": "/users"})

    body, status_code, headers = response_adapter.received_response
    assert status_code == 405
    assert "405" in body
    assert "Method Not Allowed" in body
    assert headers == {
        "Content-Type": "text/html; charset=utf-8",
        "Allow": "GET"
    }

def test_application_returns_500_for_unhandled_exception():
    app, _, response_adapter = create_application()

    @app.route("/")
    def index(request):
        raise ValueError("Unexpected error")

    app({"method": "GET", "path": "/"})

    body, status_code, headers = response_adapter.received_response

    assert status_code == 500
    assert "500" in body
    assert "Internal Server Error" in body
    assert headers == {
        "Content-Type": "text/html; charset=utf-8"
    }
    assert "Unexpected error" not in body

def test_error_handler_decorator_returns_original_handler():
    app, _, _ = create_application()

    def custom_404_handler(error):
        return ResponseModule.text_response(body="Custom 404", status_code=404)

    decorated_handler = app.errorhandler(404)(custom_404_handler)

    assert decorated_handler is custom_404_handler

def test_application_uses_custom_404_handler():
    app, _, response_adapter = create_application()
    recieved_errors = []

    @app.errorhandler(404)
    def custom_404_handler(error):
        recieved_errors.append(error)
        return ResponseModule.text_response(body="This page does not exist.", status_code=404)

    app({"method": "GET", "path": "/nonexistent"})

    assert len(recieved_errors) == 1
    assert isinstance(recieved_errors[0], NotFound)
    assert response_adapter.received_response == (
        "This page does not exist.", 404, {"Content-Type": "text/plain; charset=utf-8"}
    )

def test_application_uses_custom_405_handler():
    app, _, response_adapter = create_application()
    recieved_errors = []

    @app.route("/users", methods=["GET"])
    def users(request):
        return "Users"

    @app.errorhandler(405)
    def custom_405_handler(error):
        recieved_errors.append(error)
        allowed_methods = ", ".join(sorted(error.allowed_methods))
        return ResponseModule.text_response(
            body="Unsupported method",
            status_code=405,
            headers={"Allow": allowed_methods}
        )

    app({"method": "POST", "path": "/users"})

    assert len(recieved_errors) == 1
    assert isinstance(recieved_errors[0], MethodNotAllowed)
    assert response_adapter.received_response == (
        "Unsupported method", 405, 
        {"Content-Type": "text/plain; charset=utf-8", "Allow": "GET"}
    )

def test_application_uses_custom_500_handler():
    app, _, response_adapter = create_application()
    recieved_errors = []

    @app.route("/")
    def index(request):
        raise RuntimeError("Database unavailable")

    @app.errorhandler(500)
    def custom_500_handler(error):
        recieved_errors.append(error)
        return ResponseModule.text_response(
            body="The service is temporarily unavailable.",
            status_code=500
        )

    app({"method": "GET", "path": "/"})

    assert len(recieved_errors) == 1
    assert isinstance(recieved_errors[0], RuntimeError)
    assert str(recieved_errors[0]) == "Database unavailable"
    assert response_adapter.received_response == (
        "The service is temporarily unavailable.", 500,
        {"Content-Type": "text/plain; charset=utf-8"}
    )

def test_application_shows_exception_details_in_debug_mode():
    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()
    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter,
        debug=True
    )

    app = WebApplication(config=config)

    @app.route("/")
    def index(request):
        raise RuntimeError("Database unavailable")

    app({"method": "GET", "path": "/"})

    body, status_code, headers = response_adapter.received_response

    assert status_code == 500
    assert "RuntimeError" in body
    assert "Database unavailable" in body
    assert headers == {
        "Content-Type": "text/html; charset=utf-8"
    }

def test_custom_500_handler_has_priority_in_debug_mode():
    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()
    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter,
        debug=True
    )

    app = WebApplication(config=config)

    @app.route("/")
    def index(request):
        raise RuntimeError("Database unavailable")

    @app.errorhandler(500)
    def custom_500_handler(error):
        return ResponseModule.text_response(
            body="Custom debug error page",
            status_code=500
        )

    app({"method": "GET", "path": "/"})

    assert response_adapter.received_response == (
        "Custom debug error page", 500,
        {"Content-Type": "text/plain; charset=utf-8"}
    )