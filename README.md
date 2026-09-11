# Basic Web Backend

[![PyPI version](https://img.shields.io/pypi/v/lema-basic-web-backend.svg)](https://pypi.org/project/lema-basic-web-backend/)
[![Python versions](https://img.shields.io/pypi/pyversions/lema-basic-web-backend.svg)](https://pypi.org/project/lema-basic-web-backend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/lema2000-dev/basic_web_backend/actions/workflows/tests.yml/badge.svg)](https://github.com/lema2000-dev/basic_web_backend/actions/workflows/tests.yml)

A small Python web backend framework designed to work with
[`lema-basic-web-server`](https://github.com/lema2000-dev/basic_web_server).

The project provides:

- static and dynamic routing;
- HTTP method handling;
- request parsing;
- response helper functions;
- JSON, form and multipart request processing;
- static file serving;
- cookies;
- a lightweight template engine;
- configurable error handlers;
- application logging;
- replaceable request and response adapters.

The framework uses only the Python standard library at runtime.

## Requirements

- Python 3.10 or newer
- `lema-basic-web-server` when using the default Lema adapters

## Development installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/lema2000-dev/basic_web_backend.git
cd basic_web_backend
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
python -m pytest -v
```

## Minimal application

```python
from basic_web_backend import (
    WebApplication,
    html_response,
)
from basic_web_server import Server


app = WebApplication()


@app.route("/")
def index(request):
    return html_response(
        "<h1>Hello from Basic Web Backend!</h1>"
    )


if __name__ == "__main__":
    server = Server(app)
    server.start_console()
```

After starting the console, use the server's `run` command to select
the listening address and port.

## Routing

Routes are registered with the `route()` decorator:

```python
@app.route("/about")
def about(request):
    return html_response("<h1>About</h1>")
```

Multiple HTTP methods can be registered:

```python
@app.route(
    "/users",
    methods=["GET", "POST"],
)
def users(request):
    return html_response("<h1>Users</h1>")
```

### Dynamic routes

Supported route converters:

| Converter | Example | Python value |
|---|---|---|
| `string` | `/users/<string:name>` | `str` |
| `int` | `/users/<int:user_id>` | `int` |
| `float` | `/values/<float:value>` | `float` |
| `path` | `/files/<path:filename>` | `str` |

Example:

```python
@app.route("/users/<int:user_id>")
def user_profile(request, user_id):
    return html_response(
        f"<h1>User {user_id}</h1>"
    )
```

The `path` converter can contain `/` characters and must be the final
route segment.

## Request data

A view receives a backend `Request` object:

```python
@app.route("/search")
def search(request):
    query = request.query.get(
        "query",
        [""],
    )[0]

    return html_response(
        f"<p>Search: {query}</p>"
    )
```

Frequently used request attributes and methods:

```python
request.method
request.path
request.query_string
request.query
request.headers
request.body

request.get_header("Content-Type")
request.get_headers("Cookie")
request.cookies
```

### JSON

```python
@app.route("/api/users", methods=["POST"])
def create_user(request):
    data = request.get_json()

    return json_response(
        {
            "name": data["name"],
            "created": True,
        },
        status_code=201,
    )
```

### URL-encoded forms

```python
form = request.get_form()
username = form["username"][0]
```

### Multipart forms and file uploads

```python
form, files = request.get_multipart()

description = form["description"][0]
uploaded_file = files["document"][0]

uploaded_file.filename
uploaded_file.content_type
uploaded_file.body
uploaded_file.headers
```

Repeated fields and files are preserved as lists.

## Response helpers

The public response helpers are:

```python
content_response()
html_response()
text_response()
json_response()
file_response()
redirect_response()
empty_response()
set_cookie()
delete_cookie()
```

Examples:

```python
return text_response(
    "Application is running"
)
```

```python
return json_response(
    {"successful": True},
    status_code=200,
)
```

```python
return redirect_response(
    "/login",
    status_code=302,
)
```

```python
return empty_response(
    status_code=204
)
```

### Character encoding

Text, HTML and JSON responses support configurable character encoding:

```python
return html_response(
    "<h1>Hello</h1>",
    charset="utf-16",
)
```

## Cookies

```python
response = json_response(
    {"authenticated": True}
)

return set_cookie(
    response=response,
    key="session_id",
    value="abc123",
    max_age=3600,
    secure=True,
    http_only=True,
    same_site="Lax",
)
```

Delete a cookie:

```python
response = text_response("Logged out")

return delete_cookie(
    response=response,
    key="session_id",
)
```

## Static files

Static files are served from the `static` directory by default:

```text
static/
├── css/
│   └── style.css
└── js/
    └── application.js
```

They are available under:

```text
/static/css/style.css
/static/js/application.js
```

Custom configuration:

```python
from basic_web_backend import (
    ApplicationConfig,
    WebApplication,
)


config = ApplicationConfig(
    static_folder="assets",
    static_url_path="/assets",
)

app = WebApplication(config=config)
```

Disable built-in static file serving:

```python
config = ApplicationConfig(
    static_folder=None
)
```

The static file handler prevents paths from escaping the configured
static directory.

## Template engine

Templates are loaded from the `templates` directory by default.

Example template:

```html
<h1>Hello, {{ username }}!</h1>

{% if active %}
<p>Your account is active.</p>
{% else %}
<p>Your account is inactive.</p>
{% endif %}

<ul>
{% for item in items %}
    <li>{{ item.name }}</li>
{% endfor %}
</ul>
```

Render the template from a view:

```python
@app.route("/users/<string:username>")
def profile(request, username):
    return app.render_template(
        "profile.html",
        username=username,
        active=True,
        items=[
            {"name": "First"},
            {"name": "Second"},
        ],
    )
```

Template output is HTML-escaped by default.

Template configuration:

```python
config = ApplicationConfig(
    template_folder="templates",
    template_encoding="utf-8",
    template_autoescape=True,
    template_cache=True,
    template_auto_reload=False,
)
```

## HTTP errors

Views can raise public HTTP exceptions:

```python
from basic_web_backend import (
    BadRequest,
    NotFound,
)


@app.route("/products/<int:product_id>")
def product(request, product_id):
    if product_id == 0:
        raise NotFound(
            path=request.path
        )

    if product_id < 0:
        raise BadRequest(
            "Product ID cannot be negative."
        )

    return html_response(
        f"<h1>Product {product_id}</h1>"
    )
```

Supported HTTP exceptions include:

- `BadRequest` — 400
- `Unauthorized` — 401
- `Forbidden` — 403
- `NotFound` — 404
- `MethodNotAllowed` — 405
- `Conflict` — 409
- `PayloadTooLarge` — 413
- `UnsupportedMediaType` — 415
- `UnprocessableContent` — 422

### Custom error handlers

```python
@app.errorhandler(404)
def handle_not_found(error):
    return html_response(
        "<h1>Custom 404 page</h1>",
        status_code=404,
    )
```

```python
@app.errorhandler(500)
def handle_internal_error(error):
    return html_response(
        "<h1>The service is unavailable</h1>",
        status_code=500,
    )
```

Unexpected exceptions produce a generic 500 response in production
mode. Debug mode includes exception details in the response and must
not be enabled in production.

## Logging

Enable rotating application logs through `ApplicationConfig`:

```python
config = ApplicationConfig(
    log_file="logs/backend.log",
    log_level="INFO",
    log_max_bytes=1_000_000,
    log_backup_count=5,
)

app = WebApplication(config=config)
```

When the active log reaches the configured size, older logs are stored
as:

```text
backend.log.1
backend.log.2
backend.log.3
```

Unexpected application errors and adapter failures are logged with
their traceback. Normal 4xx client errors are not logged by the
backend.

Do not store request bodies, passwords, authorization headers or
cookie values in application logs.

## Custom server adapters

A request adapter must provide:

```python
class CustomRequestAdapter:
    def convert(self, server_request):
        return Request(
            method=server_request.method,
            path=server_request.path,
            query_string=server_request.query_string,
            headers=server_request.headers,
            body=server_request.body,
        )
```

It must return a backend `Request` object.

A response adapter must provide:

```python
class CustomResponseAdapter:
    def convert(self, backend_response):
        return backend_response
```

Configure them with:

```python
config = ApplicationConfig(
    request_adapter=CustomRequestAdapter(),
    response_adapter=CustomResponseAdapter(),
)

app = WebApplication(config=config)
```

A response adapter failure is logged and then propagated to the web
server, because a failed response adapter cannot safely convert a
backend-generated error response.

## Version

```python
import basic_web_backend

print(basic_web_backend.__version__)
```

## License

This project is licensed under the
[MIT License](LICENSE).