import pytest

from basic_web_backend.adapters import LemaRequestAdapter, LemaResponseAdapter
from basic_web_backend.config import ApplicationConfig

def test_application_config_uses_default_adapters():
    config = ApplicationConfig()

    assert isinstance(config.request_adapter, LemaRequestAdapter)
    assert isinstance(config.response_adapter, LemaResponseAdapter)

def test_application_config_accepts_custom_adapters():
    class CustomRequestAdapter:
        pass

    class CustomResponseAdapter:
        pass

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