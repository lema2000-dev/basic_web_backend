from basic_web_server.request import Request as ServerRequest
from basic_web_server.response import Response as ServerResponse

from basic_web_backend.application import WebApplication
from basic_web_backend.config import ApplicationConfig
from basic_web_backend.response import html_response

def test_application_integrates_with_basic_web_server():
    app = WebApplication()

    @app.route("/users/<int:user_id>")
    def user_details(request, user_id):
        assert request.query == {
            "details" : ["full"]
        }

        return html_response(
            f"<h1>User Details for User ID: {user_id}</h1>"
        )

    server_request = ServerRequest(
        b"GET /users/42?details=full HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"\r\n"
    )

    server_result = app(server_request)

    server_result = (server_result[0].decode("utf-8"), server_result[1], server_result[2])

    assert server_result == (
        "<h1>User Details for User ID: 42</h1>",
        200,
        {"Content-Type" : "text/html; charset=utf-8"}
    )

    server_response = ServerResponse(*server_result)
    assert isinstance(server_response, ServerResponse)

def test_application_response_can_be_serialized_by_server(
    tmp_path,
):
    config = ApplicationConfig(
        static_folder=None,
        template_folder=tmp_path,
    )

    app = WebApplication(config=config)

    @app.route("/")
    def index(request):
        return html_response(
            "<h1>Hello</h1>"
        )

    server_request = ServerRequest(
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"\r\n"
    )

    body, status_code, headers = app(
        server_request
    )

    server_response = ServerResponse(
        body=body,
        status_code=status_code,
        headers=headers,
    )

    serialized_response = (
        server_response.to_bytes()
    )

    assert serialized_response.startswith(
        b"HTTP/1.1 200 OK\r\n"
    )
    assert (
        b"Content-Type: "
        b"text/html; charset=utf-8\r\n"
        in serialized_response
    )
    assert (
        b"Content-Length: 14\r\n"
        in serialized_response
    )
    assert serialized_response.endswith(
        b"<h1>Hello</h1>"
    )

def test_internal_error_can_be_serialized_by_server(
    tmp_path,
):
    log_file = tmp_path / "backend.log"

    config = ApplicationConfig(
        static_folder=None,
        template_folder=tmp_path,
        logger_name=(
            "test.integration.internal_error"
        ),
        log_file=log_file,
        log_level="ERROR",
    )

    app = WebApplication(config=config)

    @app.route("/")
    def index(request):
        raise RuntimeError(
            "Example application failure"
        )

    server_request = ServerRequest(
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"\r\n"
    )

    body, status_code, headers = app(
        server_request
    )

    server_response = ServerResponse(
        body=body,
        status_code=status_code,
        headers=headers,
    )

    serialized_response = (
        server_response.to_bytes()
    )

    assert serialized_response.startswith(
        b"HTTP/1.1 500 "
        b"Internal Server Error\r\n"
    )
    assert serialized_response.endswith(
        b"<h1>500 Internal Server Error</h1>"
    )

    for handler in app.logger.handlers:
        handler.flush()

    log_content = log_file.read_text(
        encoding="utf-8"
    )

    assert (
        "Example application failure"
        in log_content
    )
    assert "GET /" in log_content
    assert "Traceback" in log_content

def test_server_manages_content_length(
    tmp_path,
):
    config = ApplicationConfig(
        static_folder=None,
        template_folder=tmp_path,
    )

    app = WebApplication(config=config)

    @app.route("/")
    def index(request):
        return html_response(
            "Hello",
            headers={
                "Content-Length": "999",
            },
        )

    server_request = ServerRequest(
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"\r\n"
    )

    body, status_code, headers = app(
        server_request
    )

    assert all(
        name.lower() != "content-length"
        for name in headers
    )

    server_response = ServerResponse(
        body=body,
        status_code=status_code,
        headers=headers,
    )

    serialized_response = (
        server_response.to_bytes()
    )

    assert (
        b"Content-Length: 5\r\n"
        in serialized_response
    )
    assert (
        b"Content-Length: 999\r\n"
        not in serialized_response
    )