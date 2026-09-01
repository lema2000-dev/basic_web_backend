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