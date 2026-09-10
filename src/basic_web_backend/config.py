import codecs
import logging

from .adapters import LemaRequestAdapter, LemaResponseAdapter

def _validate_adapter(adapter, name):
    convert = getattr(adapter, "convert", None)

    if not callable(convert):
        raise TypeError(f"{name} must have a callable 'convert' method")

def _validate_boolean(value, name):
    if not isinstance(value, bool):
        raise TypeError(
            f"{name} must be a boolean."
        )


def _validate_optional_non_negative_integer(
    value,
    name,
):
    if value is None:
        return

    _validate_non_negative_integer(
        value=value,
        name=name,
    )


def _validate_non_negative_integer(
    value,
    name,
):
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
    ):
        raise TypeError(
            f"{name} must be an integer."
        )

    if value < 0:
        raise ValueError(
            f"{name} cannot be negative."
        )


def _validate_static_url_path(value):
    if not isinstance(value, str):
        raise TypeError(
            "static_url_path must be text."
        )

    if not value:
        raise ValueError(
            "static_url_path cannot be empty."
        )

    if not value.startswith("/"):
        raise ValueError(
            "static_url_path must start "
            "with '/'."
        )


def _validate_encoding(encoding):
    if not isinstance(encoding, str):
        raise TypeError(
            "template_encoding must be text."
        )

    try:
        codecs.lookup(encoding)
    except LookupError as error:
        raise ValueError(
            "Unknown template encoding: "
            f"{encoding!r}."
        ) from error


def _validate_logger_name(name):
    if not isinstance(name, str):
        raise TypeError(
            "logger_name must be text."
        )

    if not name.strip():
        raise ValueError(
            "logger_name cannot be empty."
        )


def _validate_log_level(log_level):
    if not isinstance(log_level, str):
        raise TypeError(
            "log_level must be text."
        )

    normalized_level = log_level.upper()

    level = (
        logging.getLevelNamesMapping().get(
            normalized_level
        )
    )

    if level is None:
        raise ValueError(
            f"Invalid log level: {log_level!r}."
        )

class ApplicationConfig:
    def __init__(
        self,
        request_adapter=None,
        response_adapter=None,
        debug=False,
        static_folder="static",
        static_url_path="/static",
        max_content_length=None,
        template_folder="templates",
        template_encoding="utf-8",
        template_autoescape=True,
        template_cache=True,
        template_auto_reload=False,
        logger_name="basic_web_backend",
        log_file=None,
        log_level="INFO",
        log_max_bytes=1_000_000,
        log_backup_count=5
    ):
        if request_adapter is None:
            request_adapter = LemaRequestAdapter()

        if response_adapter is None:
            response_adapter = LemaResponseAdapter()

        _validate_adapter(request_adapter, "request_adapter")

        _validate_adapter(response_adapter, "response_adapter")

        _validate_adapter(
            request_adapter,
            "request_adapter",
        )

        _validate_adapter(
            response_adapter,
            "response_adapter",
        )

        _validate_boolean(
            debug,
            "debug",
        )
        _validate_boolean(
            template_autoescape,
            "template_autoescape",
        )
        _validate_boolean(
            template_cache,
            "template_cache",
        )
        _validate_boolean(
            template_auto_reload,
            "template_auto_reload",
        )

        _validate_optional_non_negative_integer(
            value=max_content_length,
            name="max_content_length",
        )

        _validate_static_url_path(
            static_url_path
        )

        _validate_encoding(
            template_encoding
        )

        _validate_logger_name(
            logger_name
        )

        _validate_log_level(
            log_level
        )

        _validate_non_negative_integer(
            value=log_max_bytes,
            name="log_max_bytes",
        )
        _validate_non_negative_integer(
            value=log_backup_count,
            name="log_backup_count",
        )

        self.request_adapter = request_adapter
        self.response_adapter = response_adapter
        self.debug = debug
        self.template_folder = template_folder
        self.template_encoding = template_encoding
        self.template_autoescape = template_autoescape
        self.template_cache = template_cache
        self.template_auto_reload = template_auto_reload
        self.static_folder = static_folder
        self.static_url_path = static_url_path
        self.max_content_length = max_content_length

        self.logger_name = logger_name
        self.log_file = log_file
        self.log_level = log_level
        self.log_max_bytes = log_max_bytes
        self.log_backup_count = log_backup_count


