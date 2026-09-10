from dataclasses import dataclass
from pathlib import Path

from ..exceptions import TemplateNotFound, TemplateLoadError
from .evaluator import render as render_nodes
from .lexer import tokenize
from .parser import parse

@dataclass
class CachedTemplate:
    nodes: list
    modified_time_ns: int
    file_size: int

class TemplateEnvironment:
    def __init__(
        self,
        template_folder,
        encoding="utf-8",
        autoescape=True,
        cache_enabled=True,
        auto_reload=False
    ):
        self.template_folder = Path(template_folder).resolve()
        self.encoding = encoding
        self.autoescape = autoescape
        self.cache_enabled = cache_enabled
        self.auto_reload = auto_reload

        self._template_cache = {}

    def render(self, template_name, **context):
        template_name = str(template_name)
        template_path = self._resolve_template_path(template_name)

        nodes = self._get_template_nodes(template_name=template_name, template_path=template_path)

        return render_nodes(
            nodes=nodes,
            context=context,
            autoescape=self.autoescape,
            template_name=template_name
        )

    def clear_cache(self, template_name=None):
        if template_name is None:
            self._template_cache.clear()
            return

        template_path = self._build_template_path(template_name)

        self._template_cache.pop(template_path, None)

    def _resolve_template_path(self, template_name):
        template_path = self._build_template_path(template_name)

        if not template_path.is_relative_to(self.template_folder):
            raise TemplateNotFound(template_name)

        if not template_path.is_file():
            raise TemplateNotFound(template_name)

        return template_path

    def _build_template_path(self, template_name):
        template_path = self.template_folder / template_name
        return template_path.resolve()        

    def _get_template_nodes(self, template_name, template_path):
        if not self.cache_enabled:
            return self._load_template_nodes(template_name, template_path)

        cached_template = self._template_cache.get(template_path)
        if cached_template is not None:
            if not self.auto_reload:
                return cached_template.nodes

            if not self._template_changed(template_name, template_path=template_path, cached_template=cached_template):
                return cached_template.nodes

        nodes = self._load_template_nodes(template_name=template_name, template_path=template_path)

        file_status = self._get_file_status(template_name=template_name, template_path=template_path)
        self._template_cache[template_path] = CachedTemplate(nodes=nodes, modified_time_ns=file_status.st_mtime_ns, file_size=file_status.st_size)

        return nodes

    def _load_template_nodes(self, template_name, template_path):
        try:
            source = template_path.read_text(encoding=self.encoding)
        except (OSError, UnicodeError) as error:
            raise TemplateLoadError(template_name=template_name, message=str(error)) from error

        tokens = tokenize(source, template_name=template_name)
        nodes = parse(tokens, template_name=template_name)
        return nodes

    def _get_file_status(self, template_name, template_path):
        try:
            return template_path.stat()
        except OSError as error:
            raise TemplateLoadError(template_name=template_name, message=str(error)) from error

    def _template_changed(self, template_name, template_path, cached_template):
        file_status = self._get_file_status(template_name=template_name, template_path=template_path)
        return (
            file_status.st_mtime_ns != cached_template.modified_time_ns or
            file_status.st_size != cached_template.file_size
        )
    