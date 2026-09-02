from basic_web_backend.application import WebApplication
from basic_web_backend.config import ApplicationConfig
from basic_web_backend.request import Request 

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
    