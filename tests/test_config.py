import pytest
import re

from basic_web_backend.adapters import LemaRequestAdapter, LemaResponseAdapter
from basic_web_backend.config import ApplicationConfig

def test_application_config_uses_default_adapters():
    config = ApplicationConfig()

    assert isinstance(config.request_adapter, LemaRequestAdapter)
    assert isinstance(config.response_adapter, LemaResponseAdapter)

def test_application_config_accepts_custom_adapters():
    class CustomRequestAdapter:
        def convert(self, server_request):
            return server_request

    class CustomResponseAdapter:
        def convert(self, response):
            return response

    custom_request_adapter = CustomRequestAdapter()
    custom_response_adapter = CustomResponseAdapter()

    config = ApplicationConfig(
        request_adapter=custom_request_adapter,
        response_adapter=custom_response_adapter
    )

    assert config.request_adapter is custom_request_adapter
    assert config.response_adapter is custom_response_adapter

def test_application_configs_have_separate_default_adapters():
    config1 = ApplicationConfig()
    config2 = ApplicationConfig()

    assert config1.request_adapter is not config2.request_adapter
    assert config1.response_adapter is not config2.response_adapter 

def test_application_config_debug_by_default():
    config = ApplicationConfig()
    assert config.debug is False

def test_application_config_accepts_debug_mode():
    config = ApplicationConfig(debug=True)
    assert config.debug is True

def test_application_config_has_default_static_settings():
    config = ApplicationConfig()

    assert config.static_folder == "static"
    assert config.static_url_path == "/static"


def test_application_config_accepts_custom_static_settings(
    tmp_path,
):
    static_folder = tmp_path / "assets"

    config = ApplicationConfig(
        static_folder=static_folder,
        static_url_path="/assets",
    )

    assert config.static_folder == static_folder
    assert config.static_url_path == "/assets"


def test_application_config_can_disable_static_files():
    config = ApplicationConfig(
        static_folder=None
    )

    assert config.static_folder is None

def test_application_config_has_no_body_size_limit_by_default():
    config = ApplicationConfig()

    assert config.max_content_length is None


def test_application_config_accepts_maximum_content_length():
    config = ApplicationConfig(
        max_content_length=1024
    )

    assert config.max_content_length == 1024

def test_config_stores_template_settings(tmp_path):
    template_folder = tmp_path / "templates"

    config = ApplicationConfig(
        template_folder=template_folder,
        template_encoding="utf-16",
        template_autoescape=False,
        template_cache=False,
        template_auto_reload=True
    )

    assert config.template_folder == template_folder
    assert config.template_encoding == "utf-16"
    assert config.template_autoescape is False
    assert config.template_cache is False
    assert config.template_auto_reload is True

def test_config_has_default_template_settings():
    config = ApplicationConfig()

    assert config.template_folder == "templates"
    assert config.template_encoding == "utf-8"
    assert config.template_autoescape is True
    assert config.template_cache is True
    assert config.template_auto_reload is False

def test_config_rejects_request_adapter_without_convert():
    class InvalidRequestAdapter:
        pass

    expected_message = (
        "request_adapter must have a callable "
        "'convert' method"
    )

    with pytest.raises(TypeError, match=re.escape(expected_message)):
        ApplicationConfig(request_adapter=InvalidRequestAdapter())

def test_config_rejects_response_adapter_without_convert():
    class InvalidResponseAdapter:
        pass

    expected_message = (
        "response_adapter must have a callable "
        "'convert' method"
    )

    with pytest.raises(TypeError, match=re.escape(expected_message)):
        ApplicationConfig(response_adapter=InvalidResponseAdapter())

def test_config_rejects_non_callable_convert_attribute():
    class InvalidRequestAdapter:
        convert = "not callable"

    expected_message = (
        "request_adapter must have a callable "
        "'convert' method"
    )

    with pytest.raises(TypeError, match=re.escape(expected_message)):
        ApplicationConfig(request_adapter=InvalidRequestAdapter())

def test_config_has_default_logging_settings():
    config = ApplicationConfig()

    assert config.logger_name == "basic_web_backend"
    assert config.log_file is None
    assert config.log_level == "INFO"
    assert config.log_max_bytes == 1_000_000
    assert config.log_backup_count == 5

def test_config_accepts_custom_logging_settings(tmp_path):
    log_file = tmp_path / "backend.log"

    config = ApplicationConfig(
        logger_name="test.backend",
        log_file=log_file,
        log_level="ERROR",
        log_max_bytes=2000,
        log_backup_count=2,
    )

    assert config.logger_name == "test.backend"
    assert config.log_file == log_file
    assert config.log_level == "ERROR"
    assert config.log_max_bytes == 2000
    assert config.log_backup_count == 2
  