class BackendError(Exception):
    """Base class for all backend-specific exceptions."""

class RoutingError(BackendError):
    """Base class for route registration errors."""

class DuplicateRouteError(RoutingError):
    """Raised when a route is registered more than once."""

class HTTPException(BackendError):
    """Base class for errors that can be converted to HTTP responses."""

    def __init__(self, status_code, reason, message=None):
        self.status_code = status_code
        self.reason = reason

        if message is None:
            message = f"{status_code} {reason}"

        super().__init__(message)

class NotFound(HTTPException):
    """Raised when no route matches the requested path."""

    def __init__(self, path):
        self.path = path
        super().__init__(status_code=404, reason="Not Found", message=f"No route was found for path: {path}")

class MethodNotAllowed(HTTPException):
    """Raised when a path exists but does not accept the requested HTTP method."""

    def __init__(self, method, path, allowed_methods):
        self.method = method.upper()
        self.path = path
        self.allowed_methods = tuple(
            sorted(allowed_method.upper() for allowed_method in allowed_methods)
        )

        super().__init__(
            status_code=405,
            reason="Method Not Allowed",
            message=f"Method {self.method} is not allowed for path: {self.path}."
        )
        