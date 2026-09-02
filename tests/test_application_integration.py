from basic_web_server.request import Request as ServerRequest
from basic_web_server.response import Response as ServerResponse

from basic_web_backend.application import WebApplication
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


    assert server_result == (
        "<h1>User Details for User ID: 42</h1>",
        200,
        {"Content-Type" : "text/html; charset=utf-8"}
    )

    server_response = ServerResponse(*server_result)
    assert isinstance(server_response, ServerResponse)