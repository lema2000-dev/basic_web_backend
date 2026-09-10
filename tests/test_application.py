import pytest

from basic_web_backend.application import WebApplication
from basic_web_backend.config import ApplicationConfig
from basic_web_backend.request import Request
from basic_web_backend.exceptions import (
    BadRequest,
    Conflict,
    Forbidden,
    MethodNotAllowed,
    NotFound,
    PayloadTooLarge,
    Unauthorized,
    UnprocessableContent,
    UnsupportedMediaType,
)
import basic_web_backend.response as ResponseModule
from basic_web_backend.template.environment import TemplateEnvironment

class FakeRequestAdapter:
    def __init__(self):
        self.received_server_request = None

    def convert(self, server_request):
        self.received_server_request = server_request
        return Request(
            method=server_request["method"],
            path=server_request["path"],
            headers=server_request.get("headers"),
            body=server_request.get("body", b""),
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
    assert "404" in body.decode("utf-8")
    assert "Not Found" in body.decode("utf-8")
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
    assert "405" in body.decode("utf-8")
    assert "Method Not Allowed" in body.decode("utf-8")
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

    body = body.decode("utf-8")

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
        ("This page does not exist.").encode("utf-8"), 404, {"Content-Type": "text/plain; charset=utf-8"}
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
        "Unsupported method".encode("utf-8"), 405, 
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
        "The service is temporarily unavailable.".encode("utf-8"), 500,
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

    body = body.decode("utf-8")

    
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
        "Custom debug error page".encode("utf-8"), 500,
        {"Content-Type": "text/plain; charset=utf-8"}
    )

def test_application_converts_bad_request_to_400_response():
    app, _, response_adapter = create_application()

    @app.route("/products")
    def products(request):
        raise BadRequest(
            "The price query parameter must be a number."
        )

    app(
        {
            "method": "GET",
            "path": "/products",
        }
    )

    body, status_code, headers = (
        response_adapter.received_response
    )

    body = body.decode("utf-8")

    assert status_code == 400
    assert "400 Bad Request" in body
    assert (
        "The price query parameter must be a number."
        in body
    )
    assert headers == {
        "Content-Type": "text/html; charset=utf-8",
    }

@pytest.mark.parametrize(
    ("error", "expected_status_code"),
    [
        (Unauthorized(), 401),
        (Forbidden(), 403),
        (Conflict(), 409),
        (PayloadTooLarge(), 413),
        (UnsupportedMediaType(), 415),
        (UnprocessableContent(), 422),
    ],
)
def test_application_handles_http_exceptions(
    error,
    expected_status_code,
):
    app, _, response_adapter = create_application()

    @app.route("/")
    def index(request):
        raise error

    app(
        {
            "method": "GET",
            "path": "/",
        }
    )

    _, status_code, _ = (
        response_adapter.received_response
    )

    assert status_code == expected_status_code

def test_application_serves_static_file(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    css_file = static_folder / "style.css"
    css_file.write_text(
        "body { color: blue; }",
        encoding="utf-8",
    )

    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter,
        static_folder=static_folder,
    )

    app = WebApplication(config=config)

    result = app(
        {
            "method": "GET",
            "path": "/static/style.css",
        }
    )

    expected_response = (
        b"body { color: blue; }",
        200,
        {
            "Content-Type": "text/css",
        },
    )

    assert (
        response_adapter.received_response
        == expected_response
    )
    assert result == {
        "converted": expected_response,
    }

def test_application_accepts_custom_static_url_path(
    tmp_path,
):
    static_folder = tmp_path / "assets"
    static_folder.mkdir()

    javascript_file = (
        static_folder / "application.js"
    )
    javascript_file.write_text(
        "console.log('Hello');",
        encoding="utf-8",
    )

    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter,
        static_folder=static_folder,
        static_url_path="/assets",
    )

    app = WebApplication(config=config)

    app(
        {
            "method": "GET",
            "path": "/assets/application.js",
        }
    )

    assert response_adapter.received_response == (
        b"console.log('Hello');",
        200,
        {
            "Content-Type": "application/javascript",
        },
    )

def test_application_can_disable_static_files(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    css_file = static_folder / "style.css"
    css_file.write_text(
        "body {}",
        encoding="utf-8",
    )

    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter,
        static_folder=None,
    )

    app = WebApplication(config=config)

    app(
        {
            "method": "GET",
            "path": "/static/style.css",
        }
    )

    _, status_code, _ = (
        response_adapter.received_response
    )

    assert status_code == 404

def test_static_route_only_accepts_get_method(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    css_file = static_folder / "style.css"
    css_file.write_text(
        "body {}",
        encoding="utf-8",
    )

    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter,
        static_folder=static_folder,
    )

    app = WebApplication(config=config)

    app(
        {
            "method": "POST",
            "path": "/static/style.css",
        }
    )

    body, status_code, headers = (
        response_adapter.received_response
    )

    body = body.decode("utf-8")

    assert status_code == 405
    assert "Method Not Allowed" in body
    assert headers["Allow"] == "GET"

def test_application_rejects_body_larger_than_limit():
    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter,
        static_folder=None,
        max_content_length=5,
    )

    app = WebApplication(config=config)
    view_was_called = False

    @app.route("/upload", methods=["POST"])
    def upload(request):
        nonlocal view_was_called
        view_was_called = True
        return "Uploaded"

    app(
        {
            "method": "POST",
            "path": "/upload",
            "body": b"123456",
        }
    )

    body, status_code, headers = (
        response_adapter.received_response
    )

    body = body.decode("utf-8")

    assert view_was_called is False
    assert status_code == 413
    assert "Payload Too Large" in body
    assert headers == {
        "Content-Type": "text/html; charset=utf-8",
    }

def test_application_accepts_body_at_size_limit():
    request_adapter = FakeRequestAdapter()
    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=request_adapter,
        response_adapter=response_adapter,
        static_folder=None,
        max_content_length=5,
    )

    app = WebApplication(config=config)

    @app.route("/upload", methods=["POST"])
    def upload(request):
        return "Uploaded"

    result = app(
        {
            "method": "POST",
            "path": "/upload",
            "body": b"12345",
        }
    )

    assert result == {
        "converted": "Uploaded",
    }

def test_application_creates_template_environment(tmp_path):
    template_folder = tmp_path / "templates"

    config = ApplicationConfig(
        template_folder=template_folder,
        template_encoding="utf-16",
        template_autoescape=False,
        template_cache=False,
        template_auto_reload=True,
    )

    app = WebApplication(config=config)

    enviroment = app.template_environment

    assert isinstance(enviroment, TemplateEnvironment)
    assert enviroment.template_folder == template_folder
    assert enviroment.encoding == "utf-16"
    assert enviroment.autoescape is False
    assert enviroment.cache_enabled is False
    assert enviroment.auto_reload is True

def test_application_renders_template(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()
    template_file = template_folder / "profile.html"
    template_file.write_text("<h1>Hello, {{ username }}!</h1>", encoding="utf-8")

    config = ApplicationConfig(
        template_folder=template_folder,
    )

    app = WebApplication(config=config)

    body, status_code, headers = app.render_template("profile.html", username="Martin")

    assert body.decode("utf-8") == "<h1>Hello, Martin!</h1>"
    assert status_code == 200
    assert headers == {
        "Content-Type": "text/html; charset=utf-8"
    }

    def test_application_template_response_accepts_options(tmp_path):
        template_folder = tmp_path / "templates"
        template_folder.mkdir()
        template_file = template_folder / "created.html"
        template_file.write_text("<h1>{{ message }}</h1>", encoding="utf-8")

        app = WebApplication(config=ApplicationConfig(template_folder=template_folder))

        body, status_code, headers = app.render_template(
            "created.html",
            message="Created",
            status_code=201,
            headers={"Location": "/items/1"},
            charset="utf-16"
        )

        assert body.decode("utf-16") == "<h1>Created</h1>"
        assert status_code == 201
        assert headers == {
            "Location": "/items/1",
            "Content-Type": "text/html; charset=utf-16"
        }

@pytest.mark.parametrize(
    "status_code", [
        "500",
        None,
        True,
    ],
)
def test_errorhandler_rejects_non_integer_status_code(
    status_code,
):
    app, _, _ = create_application()

    with pytest.raises(TypeError):
        app.errorhandler(status_code)

@pytest.mark.parametrize(
    "status_code", [
        399,
        600,
    ],
)
def test_errorhandler_rejects_non_error_status_code(
    status_code,
):
    app, _, _ = create_application()

    with pytest.raises(ValueError):
        app.errorhandler(status_code)

def test_errorhandler_rejects_non_callable_handler():
    app, _, _ = create_application()

    decorator = app.errorhandler(500)

    with pytest.raises(TypeError):
        decorator("not callable")

def test_errorhandler_rejects_duplicate_handler():
    app, _, _ = create_application()

    @app.errorhandler(500)
    def first_handler(error):
        return "First handler"

    with pytest.raises(ValueError):
        @app.errorhandler(500)
        def second_handler(error):
            return "Second handler"

def test_duplicate_errorhandler_preserves_original():
    app, _, _ = create_application()

    def first_handler(error):
        return "First handler"

    app.errorhandler(500)(first_handler)

    with pytest.raises(ValueError):
        app.errorhandler(500)(lambda error: "Second handler")

    assert app.error_handlers[500] is first_handler

def test_application_handles_error_handler_failure():
    app, _, response_adapter = create_application()

    @app.errorhandler(404)
    def broken_not_found_handler(error):
        raise RuntimeError("The 404 handler failed")

    app({"method": "GET", "path": "/missing"})

    body, status_code, headers = response_adapter.received_response

    assert status_code == 500
    assert body.decode("utf-8") == "<h1>500 Internal Server Error</h1>"

def test_custom_500_handler_handles_http_failure():
    app, _, response_adapter = create_application()

    recieved_errors = []

    @app.errorhandler(404)
    def broken_not_found_handler(error):
        raise RuntimeError("The 404 handler failed")

    @app.errorhandler(500)
    def internal_error_handler(error):
        recieved_errors.append(error)

        return ResponseModule.text_response("Custom internal error", status_code=500)

    app({"method": "GET", "path": "/missing"})

    assert len(recieved_errors) == 1
    assert isinstance(recieved_errors[0], RuntimeError)
    assert str(recieved_errors[0]) == "The 404 handler failed"

    body, status_code, _ = response_adapter.received_response

    assert status_code == 500
    assert body.decode("utf-8") == "Custom internal error"

def test_application_falls_back_when_500_handler_fails():
    app, _, response_adapter = create_application()

    @app.route("/")
    def index(request):
        raise RuntimeError("The view failed")

    @app.errorhandler(500)
    def broken_500_handler(error):
        raise RuntimeError("The 500 handler failed")

    app({"method": "GET", "path": "/"})

    body, status_code, headers = response_adapter.received_response

    assert status_code == 500
    assert body.decode("utf-8") == "<h1>500 Internal Server Error</h1>"

    assert headers == {
        "Content-Type": "text/html; charset=utf-8"
    }

def test_application_logs_unhandled_exceptions(tmp_path):
    log_file = tmp_path / "backend.log"

    config = ApplicationConfig(
        request_adapter=FakeRequestAdapter(),
        response_adapter=FakeResponseAdapter(),
        logger_name="test.application.unhandled",
        log_file=log_file,
        log_level="ERROR",
    )

    app = WebApplication(config=config)

    @app.route("/")
    def index(request):
        raise RuntimeError("Database unavailable")

    app({"method": "GET", "path": "/"})

    for handler in app.logger.handlers:
        handler.flush()

    log_content = log_file.read_text(encoding="utf-8")

    assert "ERROR" in log_content
    assert "Database unavailable" in log_content
    assert "Traceback" in log_content
    assert "GET /" in log_content

def test_application_logs_request_adapter_failure(tmp_path):
    class BrokenRequestAdapter:
        def convert(self, server_request):
            raise RuntimeError("Request conversion failed")

    log_file = tmp_path / "backend.log"

    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=BrokenRequestAdapter(),
        response_adapter=response_adapter,
        logger_name="test.application.request_adapter",
        log_file=log_file,
        log_level="ERROR",
    )

    app = WebApplication(config=config)

    result = app({"method": "GET", "path": "/"})

    for handler in app.logger.handlers:
        handler.flush()

    log_content = log_file.read_text(encoding="utf-8")

    assert "Request conversion failed" in log_content
    assert "Traceback" in log_content

    body, status_code, headers = response_adapter.received_response

    assert status_code == 500
    assert result == {"converted": (body, status_code, headers)}

def test_application_logs_and_reraises_response_adapter_failure(tmp_path):
    adapter_error = RuntimeError("Response conversion failed")

    class BrokenResponseAdapter:
        def convert(self, response):
            raise adapter_error

    log_file = tmp_path / "backend.log"

    config = ApplicationConfig(
        request_adapter=FakeRequestAdapter(),
        response_adapter=BrokenResponseAdapter(),
        logger_name="test.application.response_adapter",
        log_file=log_file,
        log_level="ERROR",
    )

    app = WebApplication(config=config)

    @app.route("/")
    def index(request):
        return ResponseModule.text_response("Hello")

    with pytest.raises(RuntimeError, match="Response conversion failed") as error_info:
        app({"method": "GET", "path": "/"})

    assert error_info.value is adapter_error

    for handler in app.logger.handlers:
        handler.flush()

    log_content = log_file.read_text(encoding="utf-8")

    assert "The response adapter failed" in log_content
    assert "Response conversion failed" in log_content
    assert "Traceback" in log_content

@pytest.mark.parametrize(
    "setting_name",
    [
        "debug",
        "template_autoescape",
        "template_cache",
        "template_auto_reload",
    ],
)
def test_config_rejects_non_boolean_settings(
    setting_name,
):
    with pytest.raises(TypeError):
        ApplicationConfig(
            **{setting_name: "yes"}
        )

@pytest.mark.parametrize(
    "value",
    [
        -1,
        1.5,
        "1024",
        True,
    ],
)
def test_config_rejects_invalid_max_content_length(
    value,
):
    with pytest.raises(
        (TypeError, ValueError)
    ):
        ApplicationConfig(
            max_content_length=value
        )

@pytest.mark.parametrize(
    "value",
    [
        None,
        0,
        1024,
    ],
)
def test_config_accepts_valid_max_content_length(
    value,
):
    config = ApplicationConfig(
        max_content_length=value
    )

    assert config.max_content_length == value

@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "static",
        42,
    ],
)
def test_config_rejects_invalid_static_url_path(
    value,
):
    with pytest.raises(
        (TypeError, ValueError)
    ):
        ApplicationConfig(
            static_url_path=value
        )

@pytest.mark.parametrize(
    "value",
    [
        "/",
        "/static",
        "/assets",
    ],
)
def test_config_accepts_valid_static_url_path(
    value,
):
    config = ApplicationConfig(
        static_url_path=value
    )

    assert config.static_url_path == value

def test_config_rejects_unknown_template_encoding():
    with pytest.raises(ValueError):
        ApplicationConfig(
            template_encoding=(
                "unknown-example-encoding"
            )
        )

@pytest.mark.parametrize(
    "encoding",
    [
        "utf-8",
        "utf-16",
        "latin-1",
    ],
)
def test_config_accepts_known_template_encoding(
    encoding,
):
    config = ApplicationConfig(
        template_encoding=encoding
    )

    assert config.template_encoding == encoding

@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "   ",
        42,
    ],
)
def test_config_rejects_invalid_logger_name(
    value,
):
    with pytest.raises(
        (TypeError, ValueError)
    ):
        ApplicationConfig(
            logger_name=value
        )

@pytest.mark.parametrize(
    "value",
    [
        "UNKNOWN",
        "",
        None,
        42,
    ],
)
def test_config_rejects_invalid_log_level(
    value,
):
    with pytest.raises(
        (TypeError, ValueError)
    ):
        ApplicationConfig(
            log_level=value
        )

@pytest.mark.parametrize(
    ("setting_name", "value"),
    [
        ("log_max_bytes", -1),
        ("log_max_bytes", 1.5),
        ("log_max_bytes", True),
        ("log_backup_count", -1),
        ("log_backup_count", 1.5),
        ("log_backup_count", True),
    ],
)
def test_config_rejects_invalid_log_rotation_setting(
    setting_name,
    value,
):
    with pytest.raises(
        (TypeError, ValueError)
    ):
        ApplicationConfig(
            **{setting_name: value}
        )

def test_config_accepts_disabled_log_rotation():
    config = ApplicationConfig(
        log_max_bytes=0,
        log_backup_count=0,
    )

    assert config.log_max_bytes == 0
    assert config.log_backup_count == 0

@pytest.mark.parametrize(
    "invalid_result",
    [
        None,
        object(),
        {
            "method": "GET",
            "path": "/",
        },
    ],
)
def test_application_rejects_invalid_request_adapter_result(
    invalid_result,
):
    class InvalidRequestAdapter:
        def convert(self, server_request):
            return invalid_result

    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=InvalidRequestAdapter(),
        response_adapter=response_adapter,
    )

    app = WebApplication(config=config)

    app(
        {
            "method": "GET",
            "path": "/",
        }
    )

    body, status_code, headers = (
        response_adapter.received_response
    )

    assert status_code == 500
    assert (
        body.decode("utf-8")
        == "<h1>500 Internal Server Error</h1>"
    )

def test_invalid_request_adapter_result_reaches_500_handler():
    class InvalidRequestAdapter:
        def convert(self, server_request):
            return None

    received_errors = []

    config = ApplicationConfig(
        request_adapter=InvalidRequestAdapter(),
        response_adapter=FakeResponseAdapter(),
    )

    app = WebApplication(config=config)

    @app.errorhandler(500)
    def internal_error_handler(error):
        received_errors.append(error)

        return ResponseModule.text_response(
            "Internal error",
            status_code=500,
        )

    app(
        {
            "method": "GET",
            "path": "/",
        }
    )

    assert len(received_errors) == 1
    assert isinstance(
        received_errors[0],
        TypeError,
    )
    assert str(received_errors[0]) == (
        "The request adapter must return "
        "a Request object."
    )

def test_application_accepts_request_subclass_from_adapter():
    class CustomRequest(Request):
        pass

    class CustomRequestAdapter:
        def convert(self, server_request):
            return CustomRequest(
                method="GET",
                path="/",
            )

    config = ApplicationConfig(
        request_adapter=CustomRequestAdapter(),
        response_adapter=FakeResponseAdapter(),
    )

    app = WebApplication(config=config)

    @app.route("/")
    def index(request):
        return ResponseModule.text_response(
            "Accepted"
        )

    result = app(object())

    body, status_code, _ = (
        result["converted"]
    )

    assert body.decode("utf-8") == "Accepted"
    assert status_code == 200

@pytest.mark.parametrize(
    "invalid_result",
    [
        None,
        object(),
        {
            "method": "GET",
            "path": "/",
        },
    ],
)
def test_application_rejects_invalid_request_adapter_result(
    invalid_result,
):
    class InvalidRequestAdapter:
        def convert(self, server_request):
            return invalid_result

    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=InvalidRequestAdapter(),
        response_adapter=response_adapter,
    )

    app = WebApplication(config=config)

    app(
        {
            "method": "GET",
            "path": "/",
        }
    )

    body, status_code, headers = (
        response_adapter.received_response
    )

    assert status_code == 500
    assert (
        body.decode("utf-8")
        == "<h1>500 Internal Server Error</h1>"
    )

def test_application_logs_static_file_permission_error(
    tmp_path,
    monkeypatch,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    log_file = tmp_path / "backend.log"

    response_adapter = FakeResponseAdapter()

    config = ApplicationConfig(
        request_adapter=FakeRequestAdapter(),
        response_adapter=response_adapter,
        static_folder=static_folder,
        logger_name=(
            "test.application.static_permission"
        ),
        log_file=log_file,
        log_level="ERROR",
    )

    app = WebApplication(config=config)

    def raise_permission_error(**kwargs):
        raise PermissionError(
            "Static file access denied"
        )

    monkeypatch.setattr(
        app.static_handler,
        "serve",
        raise_permission_error,
    )

    result = app(
        {
            "method": "GET",
            "path": "/static/style.css",
        }
    )

    for handler in app.logger.handlers:
        handler.flush()

    log_content = log_file.read_text(
        encoding="utf-8"
    )

    assert (
        "Static file access denied"
        in log_content
    )
    assert (
        "GET /static/style.css"
        in log_content
    )
    assert "Traceback" in log_content

    body, status_code, headers = (
        response_adapter.received_response
    )

    assert status_code == 500
    assert (
        body.decode("utf-8")
        == "<h1>500 Internal Server Error</h1>"
    )
    assert result == {
        "converted": (
            body,
            status_code,
            headers,
        )
    }