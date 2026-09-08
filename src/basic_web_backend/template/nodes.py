from dataclasses import dataclass, field

class TemplateNode:
    """Base class for template syntax nodes."""
    pass

@dataclass
class TextNode(TemplateNode):
    content: str
    line: int = 1
    column: int = 1

@dataclass
class VariableNode(TemplateNode):
    path: list[str]
    line: int = 1
    column: int = 1

@dataclass
class IfNode(TemplateNode):
    condition: list[str]
    body: list[TemplateNode] = field(default_factory=list)
    else_body: list[TemplateNode] = field(default_factory=list)
    line: int = 1
    column: int = 1

@dataclass
class ForNode(TemplateNode):
    variable_name: str
    iterable: list[str]
    body: list[TemplateNode] = field(default_factory=list)
    line: int = 1
    column: int = 1

