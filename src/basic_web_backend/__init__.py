from importlib.metadata import version

from .adapters import LemaRequestAdapter, LemaResponseAdapter
from .application import WebApplication
from .config import ApplicationConfig
from .exceptions import (
    AmbiguousRouteError,
    BackendError,
    BadRequest,
    Conflict,
    DuplicateRouteError,
    Forbidden,
    HTTPException,
    InvalidRouteError,
    MethodNotAllowed,
    NotFound,
    PayloadTooLarge,
    RoutingError,
    TemplateError,
    TemplateLoadError,
    TemplateNotFound,
    TemplateRenderError,
    TemplateSyntaxError,
    Unauthorized,
    UndefinedVariableError,
    UnprocessableContent,
    UnsupportedMediaType,
)

from .multipart import UploadedFile
from .request import Request
from .response import (
    content_response,
    delete_cookie,
    empty_response,
    file_response,
    html_response,
    json_response,
    redirect_response,
    set_cookie,
    text_response, 
)
from .template.environment import TemplateEnvironment

__version__ = version("lema-basic-web-backend")

__all__ = [
    "__version__",
    "WebApplication",
    "ApplicationConfig",
    "Request",
    "UploadedFile",
    "LemaRequestAdapter",
    "LemaResponseAdapter",
    "TemplateEnvironment",
    "content_response",
    "html_response",
    "text_response",
    "json_response",
    "file_response",
    "redirect_response",
    "empty_response",
    "set_cookie",
    "delete_cookie",
    "BackendError",
    "RoutingError",
    "DuplicateRouteError",
    "InvalidRouteError",
    "AmbiguousRouteError",
    "HTTPException",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "MethodNotAllowed",
    "Conflict",
    "PayloadTooLarge",
    "UnsupportedMediaType",
    "UnprocessableContent",
    "TemplateError",
    "TemplateNotFound",
    "TemplateLoadError",
    "TemplateSyntaxError",
    "TemplateRenderError",
    "UndefinedVariableError"
]