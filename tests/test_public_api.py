import basic_web_backend as backend
from importlib.metadata import version


def test_public_api_exports_application_objects():
    assert backend.WebApplication is not None
    assert backend.ApplicationConfig is not None


def test_public_api_exports_request_objects():
    assert backend.Request is not None
    assert backend.UploadedFile is not None


def test_public_api_exports_response_helpers():
    expected_names = [
        "content_response",
        "html_response",
        "text_response",
        "json_response",
        "file_response",
        "redirect_response",
        "empty_response",
        "set_cookie",
        "delete_cookie",
    ]

    for name in expected_names:
        assert callable(
            getattr(backend, name)
        )


def test_public_api_exports_http_exceptions():
    expected_names = [
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
    ]

    for name in expected_names:
        exception_class = getattr(
            backend,
            name,
        )

        assert issubclass(
            exception_class,
            Exception,
        )

def test_public_api_exports_routing_exceptions():
    expected_names = [
        "BackendError",
        "RoutingError",
        "DuplicateRouteError",
        "InvalidRouteError",
        "AmbiguousRouteError",
    ]

    for name in expected_names:
        exception_class = getattr(
            backend,
            name,
        )

        assert issubclass(
            exception_class,
            Exception,
        )

def test_public_api_exports_template_objects():
    expected_names = [
        "TemplateEnvironment",
        "TemplateError",
        "TemplateNotFound",
        "TemplateLoadError",
        "TemplateSyntaxError",
        "TemplateRenderError",
        "UndefinedVariableError",
    ]

    for name in expected_names:
        assert hasattr(backend, name)


def test_public_api_exports_default_adapters():
    assert backend.LemaRequestAdapter is not None
    assert backend.LemaResponseAdapter is not None


def test_public_api_defines_all():
    expected_names = {
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
    }

    assert set(backend.__all__) == (
        expected_names
    )

def test_public_api_exposes_package_version():
    assert backend.__version__ == version("lema-basic-web-backend")

