from .adapters import LemaRequestAdapter, LemaResponseAdapter

class ApplicationConfig:
    def __init__(
        self,
        request_adapter=None,
        response_adapter=None,
        debug=False,
        static_folder="static",
        static_url_path="/static",
        max_content_length=None
    ):
        if request_adapter is None:
            request_adapter = LemaRequestAdapter()

        if response_adapter is None:
            response_adapter = LemaResponseAdapter()

        self.request_adapter = request_adapter
        self.response_adapter = response_adapter
        self.debug = debug
        self.static_folder = static_folder
        self.static_url_path = static_url_path
        self.max_content_length = max_content_length