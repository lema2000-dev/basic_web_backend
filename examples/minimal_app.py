from basic_web_backend.application import WebApplication
from basic_web_backend.response import html_response

from basic_web_server.server import Server

app = WebApplication()

@app.route("/")
def index(request):
    return html_response(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Basic Web Backend Example</title>
        </head>
        <body>
            <h1>Welcome to the Basic Web Backend Example!</h1>
            <p>This is a minimal web application built using the Basic Web Backend framework.</p>
            <a href="/users/42?details=test_details">Open user 42 </a>
        </body>
        </html>
        """
    )

@app.route("/users/<int:user_id>")
def user_details(request, user_id):
    details = request.query.get("details", ["not specified"])[0]

    return html_response(
        f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>User {user_id}</title>
        </head>
        <body>
            <h1>User Details for User ID: {user_id}</h1>
            <p>Details: {details}</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """
    )

server = Server(app)
server.start_console()