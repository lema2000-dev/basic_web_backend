from .adapters import LemaRequestAdapter, LemaResponseAdapter

class ApplicationConfig:
    def __init__(self, request_adapter=None, response_adapter=None):
        self.request_adapter = request_adapter or LemaRequestAdapter()
        self.response_adapter = response_adapter or LemaResponseAdapter()

    