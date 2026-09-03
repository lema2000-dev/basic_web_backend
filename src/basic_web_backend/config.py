from .adapters import LemaRequestAdapter, LemaResponseAdapter

class ApplicationConfig:
    def __init__(
        self,
        request_adapter=None,
        response_adapter=None,
        debug=False
    ):
        if request_adapter is None:
            request_adapter = LemaRequestAdapter()

        if response_adapter is None:
            response_adapter = LemaResponseAdapter()

        self.request_adapter = request_adapter
        self.response_adapter = response_adapter
        self.debug = debug