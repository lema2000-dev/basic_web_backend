from collections.abc import Mapping
from html import escape

from ..exceptions import TemplateRenderError, UndefinedVariableError
from .nodes import TextNode, VariableNode, IfNode, ForNode

_MISSING = object()

def render(nodes, context, autoescape=True, template_name=None):
    if context is None:
        context = {}
    else:
        context = dict(context)

    return _render_nodes(nodes=nodes, context=context, autoescape=autoescape, template_name=template_name)

def _render_nodes(nodes, context, autoescape, template_name):
    output_parts = []

    for node in nodes:
        if isinstance(node, TextNode):
            output_parts.append(node.content)
            continue

        if isinstance(node, VariableNode):
            value = _resolve_variable(path=node.path, context=context)

            rendered_value = str(value)
            if autoescape:
                rendered_value = escape(rendered_value, quote=True)

            output_parts.append(rendered_value)
            continue

        if isinstance(node, IfNode):
            condition_value = _resolve_variable(path=node.condition, context=context)

            if condition_value:
                selected_nodes = node.body
            else:
                selected_nodes = node.else_body

            rendered_branch = _render_nodes(
                nodes=selected_nodes,
                context=context,
                autoescape=autoescape,
                template_name=template_name
            )

            output_parts.append(rendered_branch)
            continue

        if isinstance(node, ForNode):
            iterable_value = _resolve_variable(path=node.iterable, context=context)

            try:
                iterator = iter(iterable_value)
            except TypeError as error:
                iterable_name = '.'.join(node.iterable)
                raise TemplateRenderError(
                    f"Template value is not iterable: {iterable_name}") from error

            for item in iterator:
                local_context = dict(context)

                local_context[node.variable_name] = item
                rendered_item = _render_nodes(
                    nodes=node.body,
                    context=local_context,
                    autoescape=autoescape,
                    template_name=template_name
                )
                output_parts.append(rendered_item)
            continue

        raise TemplateRenderError(
            f"Unsupported node type: {type(node).__name__}")

    return ''.join(output_parts)

def _resolve_variable(path, context):
    variable_name = '.'.join(path)

    if not path:
        raise UndefinedVariableError(variable_name="")

    first_name = path[0]

    if first_name not in context:
        raise UndefinedVariableError(variable_name=variable_name)

    value = context[first_name]

    for name in path[1:]:
        value = _resolve_part(
            value=value,
            name=name,
            variable_name=variable_name
        )

    return value

def _resolve_part(value, name, variable_name):
    if isinstance(value, Mapping):
        if name not in value:
            raise UndefinedVariableError(variable_name=variable_name)
        return value[name]

    attribute = getattr(value, name, _MISSING)

    if attribute is _MISSING:
        raise UndefinedVariableError(variable_name=variable_name)

    return attribute
