import pytest

from basic_web_backend.exceptions import TemplateSyntaxError
from basic_web_backend.template.lexer import tokenize
from basic_web_backend.template.nodes import TextNode, VariableNode, IfNode, ForNode
from basic_web_backend.template.parser import parse

def test_parse_text_token():
    tokens = tokenize("<h1>Hello, World!</h1>")

    nodes = parse(tokens)

    assert nodes == [
        TextNode(
            content="<h1>Hello, World!</h1>",
            line=1,
            column=1
        )
    ]

def test_parse_variable_token():
    tokens = tokenize("<h1>Hello, {{ username }}!</h1>")

    nodes = parse(tokens)

    assert nodes == [
        TextNode(
            content="<h1>Hello, ",
            line=1,
            column=1
        ),
        VariableNode(
            path=["username"],
            line=1,
            column=12
        ),
        TextNode(
            content="!</h1>",
            line=1,
            column=26
        )
    ]

def test_parse_nested_variable_path():
    tokens = tokenize("{{ user.address.city }}")

    nodes = parse(tokens)

    assert nodes == [
        VariableNode(
            path=["user", "address", "city"],
            line=1,
            column=1
        )
    ]

def test_parse_rejects_empty_variable():
    tokens = tokenize("{{ }}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens, template_name="profile.html")

    error = error_info.value

    assert error.message == "Variable expression cannot be empty."
    assert error.template_name == "profile.html"
    assert error.line == 1
    assert error.column == 1

@pytest.mark.parametrize(
    "expression", [
        "user..name",
        ".user",
        "user.",
        "user-name",
        "42user",
        "user name"
    ]
)
def test_parse_rejects_invalid_variable_path(expression):
    tokens = tokenize("{{ " + expression + " }}")
    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens, template_name="profile.html")

    assert error_info.value.message == f"Invalid variable expression: {expression}"

def test_parse_rejects_unkown_statement():
    tokens = tokenize("{% unknown_statement %}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens, template_name="profile.html")

    assert error_info.value.message == "Unknown template statement: unknown_statement"
    
def test_parse_if_statement():
    tokens = tokenize("{% if authenticated %}Welcome{% endif %}")
    nodes = parse(tokens)

    assert len(nodes) == 1
    if_node = nodes[0]

    assert isinstance(if_node, IfNode)
    assert if_node.condition == ["authenticated"]
    assert if_node.body == [TextNode(
        content="Welcome",
        line=1,
        column=23
    )]

    assert if_node.else_body == []
    assert if_node.line == 1
    assert if_node.column == 1

def test_parse_if_else_statement():
    tokens = tokenize("{% if authenticated %}Welcome{% else %}Please log in{% endif %}")

    nodes = parse(tokens)

    assert len(nodes) == 1

    if_node = nodes[0]

    assert isinstance(if_node, IfNode)
    assert if_node.condition == ["authenticated"]
    assert [node.content for node in if_node.body] == ["Welcome"]
    assert [node.content for node in if_node.else_body] == ["Please log in"]

def test_parse_nested_if_statments():
    tokens = tokenize(
        "{% if user %}User exists"
        "{% if user.active %} and is active{% endif %}{% endif %}"
    )

    nodes = parse(tokens)

    outer_if = nodes[0]

    assert isinstance(outer_if, IfNode)
    assert outer_if.condition == ["user"]

    assert isinstance(outer_if.body[1], IfNode)

    inner_if = outer_if.body[1]

    assert inner_if.condition == ["user", "active"]
    assert inner_if.body[0].content == " and is active"

def test_parse_rejects_unclosed_if():
    tokens = tokenize("{% if authenticated %}Welcome")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens, template_name="profile.html")

    error = error_info.value

    assert error.message == "Missing endif statement."
    assert error.template_name == "profile.html"
    assert error.line == 1
    assert error.column == 1

def test_parse_rejects_if_without_condition():
    tokens = tokenize("{% if %}Welcome{% endif %}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens)

    assert error_info.value.message == "If statement requires a condition."

def test_parse_rejects_invalid_if_condition():
    tokens = tokenize("{% if user..authenticated %}Welcome{% endif %}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens)

    assert error_info.value.message == "Invalid variable expression: user..authenticated"

def test_parse_rejects_unexpected_else():
    tokens = tokenize("{% else %}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens)

    assert error_info.value.message == "Unexpected else statement."

def test_parse_rejects_unexpected_endif():
    tokens = tokenize("{% endif %}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens)

    assert error_info.value.message == "Unexpected endif statement."

def test_parse_for_statement():
    tokens = tokenize("{% for product in products %}{{ product.name }}{% endfor %}")

    nodes = parse(tokens)

    assert len(nodes) == 1

    for_node = nodes[0]

    assert isinstance(for_node, ForNode)
    assert for_node.variable_name == "product"
    assert for_node.iterable == ["products"]
    assert for_node.body == [
        VariableNode(
            path=["product", "name"],
            line=1,
            column=30
        )
    ]
    assert for_node.line == 1
    assert for_node.column == 1

def test_parse_for_with_nested_iterable():
    tokens = tokenize("{% for role in user.roles %}{{ role }}{% endfor %}")

    nodes = parse(tokens)

    for_node = nodes[0]

    assert isinstance(for_node, ForNode)
    assert for_node.iterable == ["user", "roles"]

def test_parse_if_inside_for():
    tokens = tokenize(
        "{% for user in users %}"
        "{% if user.active %}{{ user.name }}{% endif %}"
        "{% endfor %}"
    )

    nodes = parse(tokens)

    for_node = nodes[0]

    assert isinstance(for_node, ForNode)

    if_node = for_node.body[0]

    assert isinstance(if_node, IfNode)
    assert if_node.condition == ["user", "active"]

    assert if_node.body[0] == VariableNode(
        path=["user", "name"],
        line=1,
        column=44
    )

def test_parse_for_inside_if():
    tokens = tokenize(
        "{% if products %}"
        "{% for product in products %}{{ product.name }}{% endfor %}"
        "{% endif %}"
    )

    nodes = parse(tokens)

    if_node = nodes[0]

    assert isinstance(if_node, IfNode)
    assert len(if_node.body) == 1
    assert isinstance(if_node.body[0], ForNode)

@pytest.mark.parametrize(
    "statement", [
        "for",
        "for product",
        "for product products",
        "for in products",
        "for product in",
        "for 42product in products"
    ]
)
def test_parse_rejects_invalid_for_statement(statement):
    tokens = tokenize("{% " + statement + " %}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens)

    assert error_info.value.message == f"Invalid for statement. Expected format: 'for <variable> in <iterable>'."

def test_parse_rejects_invalid_for_iterable():
    tokens = tokenize("{% for product in products..list %}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens)

    assert error_info.value.message == "Invalid variable expression: products..list"

def test_parse_rejects_unclosed_for():
    tokens = tokenize("{% for product in products %}{{ product.name }}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens, template_name="products.html")

    error = error_info.value

    assert error.message == "Missing endfor statement."
    assert error.template_name == "products.html"
    assert error.line == 1
    assert error.column == 1

def test_parse_rejects_unexpected_endfor():
    tokens = tokenize("{% endfor %}")

    with pytest.raises(TemplateSyntaxError) as error_info:
        parse(tokens)

    assert error_info.value.message == "Unexpected endfor statement."

    