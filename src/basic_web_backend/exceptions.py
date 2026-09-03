class BackendError(Exception):
    """Base class for all backend-specific exceptions."""
    pass

class RoutingError(BackendError):
    """Base class for route registration errors."""
    pass

class DuplicateRouteError(RoutingError):
    """Raised when a route is registered more than once."""
    def __init__(self, path, method):
        self.path = path
        self.method = method
        super().__init__(f"Route alredy registered for path: {path} and method: {method}")

class InvalidRouteError(RoutingError):
    """Raised when a route is registered with an invalid path or method."""
    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__(f"Invalid route {path!r}: {message}")

class AmbiguousRouteError(RoutingError):
    """Raised when a route is registered that conflicts with an existing route."""
    def __init__(self, path, conflicting_path, methods):
        self.path = path
        self.conflicting_path = conflicting_path
        self.methods = methods

        method_list = ", ".join(sorted(self.methods))
        super().__init__(
            f"Ambigous routes {path!r} and "
            f"{conflicting_path!r} for methods: {method_list}"
        )

class HTTPException(Exception):
    """Base class for all HTTP exceptions."""
    status_code = 500
    default_message = "Internal Server Error"

    def __init__(self, message=None, headers=None):
        self.message = (
            message
            if message is not None
            else self.default_message
        )
        self.headers = dict(headers or {})

        super().__init__(self.message)


class BadRequest(HTTPException):
    status_code = 400
    default_message = "Bad Request"


class Unauthorized(HTTPException):
    status_code = 401
    default_message = "Unauthorized"


class Forbidden(HTTPException):
    status_code = 403
    default_message = "Forbidden"


class NotFound(HTTPException):
    status_code = 404
    default_message = "Not Found"

    def __init__(self, path, message=None):
        self.path = path
        super().__init__(message=message)


class MethodNotAllowed(HTTPException):
    status_code = 405
    default_message = "Method Not Allowed"

    def __init__(
        self,
        method,
        path,
        allowed_methods,
        message=None,
    ):
        self.method = method.upper()
        self.path = path
        self.allowed_methods = tuple(sorted(method.upper() for method in allowed_methods))

        allow_header = ", ".join(
            sorted(self.allowed_methods)
        )

        super().__init__(
            message=message,
            headers={
                "Allow": allow_header,
            },
        )


class Conflict(HTTPException):
    status_code = 409
    default_message = "Conflict"


class PayloadTooLarge(HTTPException):
    status_code = 413
    default_message = "Payload Too Large"


class UnsupportedMediaType(HTTPException):
    status_code = 415
    default_message = "Unsupported Media Type"


class UnprocessableContent(HTTPException):
    status_code = 422
    default_message = "Unprocessable Content"
        