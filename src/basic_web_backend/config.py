from .adapters import LemaRequestAdapter, LemaResponseAdapter

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
        template_auto_reload=False
    ):
        if request_adapter is None:
            request_adapter = LemaRequestAdapter()

        if response_adapter is None:
            response_adapter = LemaResponseAdapter()

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