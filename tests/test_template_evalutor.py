from dataclasses import dataclass
import pytest

from basic_web_backend.exceptions import TemplateRenderError, UndefinedVariableError
from basic_web_backend.template.evaluator import render
from basic_web_backend.template.nodes import ForNode, TextNode, VariableNode, IfNode

def test_render_text_node():
    nodes = [
        TextNode(
            content="<h1>Hello, World!</h1>",
        )
    ]

    result = render(nodes=nodes, context={})
    assert result == "<h1>Hello, World!</h1>"

def test_render_variable_from_context():
    nodes = [
        TextNode(
            content="<h1>Hello, ",
        ),
        VariableNode(
            path=["username"],
        ),
        TextNode(
            content="!</h1>",
        )
    ]

    result = render(nodes=nodes, context={"username": "Martin"})
    assert result == "<h1>Hello, Martin!</h1>"

def test_render_nested_dictionary_variable():
    nodes = [
        VariableNode(
            path=["user", "address", "city"],
        )
    ]

    result = render(nodes=nodes, context={"user": {"address": {"city": "New York"}}})
    assert result == "New York"

def test_render_object_attribute():
    @dataclass
    class User:
        name: str

    nodes = [
        VariableNode(
            path=["user", "name"],
        )
    ]

    result = render(nodes=nodes, context={"user": User(name="Martin")})
    assert result == "Martin"

def test_render_escapes_variable_value():
    nodes = [
        VariableNode(
            path=["content"],
        )
    ]

    result = render(nodes=nodes, context={"content": "<script>alert('example')</script>"})
    assert result == "&lt;script&gt;alert(&#x27;example&#x27;)&lt;/script&gt;"

def test_render_can_disable_autoescape():
    nodes = [
        VariableNode(
            path=["content"],
        )
    ]

    result = render(nodes=nodes, context={"content": "<strong>Bold</strong>"}, autoescape=False)
    assert result == "<strong>Bold</strong>"

def test_render_rejects_missing_variable():
    nodes = [
        VariableNode(
            path=["username"],
            line=4,
            column=8
        )
    ]

    with pytest.raises(UndefinedVariableError) as error_info:
        render(nodes=nodes, context={}, template_name="profile.html")

    error = error_info.value

    assert error.variable_name == "username"

def test_render_rejects_missing_nested_value():
    nodes = [
        VariableNode(
            path=["user", "address", "city"]
        )
    ]

    with pytest.raises(UndefinedVariableError) as error_info:
        render(nodes=nodes, context={"user": {"address": {}}}, template_name="profile.html")

    assert error_info.value.variable_name == "user.address.city"

def test_render_does_not_modify_context():
    context = {"username": "Martin"}

    nodes = [
        VariableNode(
            path=["username"]
        )
    ]

    render(nodes=nodes, context=context)

    assert context == {"username": "Martin"}

def test_render_if_true_branch():
    nodes = [
        IfNode(
            condition=["authenticated"],
            body=[
                TextNode(
                    content="<p>Welcome back!</p>"
                )
            ],
            else_body=[
                TextNode(
                    content="<p>Please log in.</p>"
                )
            ]
        )
    ]

    result = render(nodes=nodes, context={"authenticated": True})

    assert result == "<p>Welcome back!</p>"

def test_render_if_false_branch():
    nodes = [
        IfNode(
            condition=["authenticated"],
            body=[
                TextNode(
                    content="<p>Welcome back!</p>"
                )
            ],
            else_body=[
                TextNode(
                    content="<p>Please log in.</p>"
                )
            ]
        )
    ]

    result = render(nodes=nodes, context={"authenticated": False})

    assert result == "<p>Please log in.</p>"

@pytest.mark.parametrize(
    "condition_value", [
        True,
        1,
        -1,
        "Martin",
        [1],
        {"name": "Martin"}
    ]
)
def test_render_if_accepts_truthy_values(condition_value):
    nodes = [
        IfNode(
            condition=["value"],
            body=[
                TextNode(
                    content="<p>Truthy</p>"
                )
            ],
            else_body=[
                TextNode(
                    content="<p>Falsy</p>"
                )
            ]
        )
    ]

    result = render(nodes=nodes, context={"value": condition_value})

    assert result == "<p>Truthy</p>"

@pytest.mark.parametrize(
    "condition_value", [
        False,
        None,
        0,
        0.0,
        "",
        [],
        {}
    ]
)
def test_render_if_accepts_falsy_values(condition_value):
    nodes = [
        IfNode(
            condition=["value"],
            body=[
                TextNode(
                    content="<p>Truthy</p>"
                )
            ],
            else_body=[
                TextNode(
                    content="<p>Falsy</p>"
                )
            ]
        )
    ]

    result = render(nodes=nodes, context={"value": condition_value})

    assert result == "<p>Falsy</p>"

def test_render_if_ignores_unselected_branch():
    nodes = [
        IfNode(
            condition=["authenticated"],
            body=[
                TextNode(
                    content="<p>Welcome back!</p>"
                )
            ],
            else_body=[
                TextNode(
                    VariableNode(path=["missing_variable"])
                )
            ]
        )
    ]

    result = render(nodes=nodes, context={"authenticated": True})

    assert "<p>Welcome back!</p>" == result

def test_redner_nested_if_nodes():
    nodes = [
        IfNode(
            condition=["user"],
            body=[
                IfNode(
                    condition=["user", "active"],
                    body=[
                        TextNode(
                            content="<p>User is active</p>"
                        )
                    ],
                    else_body=[
                        TextNode(
                            content="<p>User is inactive</p>"
                        )
                    ]
                )
            ]
        )
    ]

    result = render(nodes=nodes, context={"user": {"active": True}})
    assert result == "<p>User is active</p>"

    result = render(nodes=nodes, context={"user": {"active": False}})
    assert result == "<p>User is inactive</p>"

def test_render_if_rejects_missing_condition():
    nodes = [
        IfNode(
            condition=["authenticated"],
            body=[
                TextNode(
                    content="<p>Welcome back!</p>"
                )
            ],
            else_body=[
                TextNode(
                    content="<p>Please log in.</p>"
                )
            ]
        )
    ]

    with pytest.raises(UndefinedVariableError) as error_info:
        render(nodes=nodes, context={})

    assert error_info.value.variable_name == "authenticated"

def test_render_for_node():
    nodes = [
        TextNode(content="<ul>"),
        ForNode(
            variable_name="product",
            iterable=["products"],
            body=[
                TextNode(content="<li>"),
                VariableNode(path=["product"]),
                TextNode(content="</li>")
            ]
        ),
        TextNode(content="</ul>")
    ]

    result = render(nodes=nodes, context={"products": ["Book", "Computer", "Phone"]})

    assert result == "<ul><li>Book</li><li>Computer</li><li>Phone</li></ul>"

def test_render_for_with_nested_values():
    nodes = [
        ForNode(
            variable_name="user",
            iterable=["users"],
            body=[
                VariableNode(path=["user", "name"]),
                TextNode(content=";")
            ]
        )
    ]

    result = render(nodes=nodes, context={"users": [{"name": "Alice"}, {"name": "Bob"}]})

    assert result == "Alice;Bob;"

def test_render_for_with_empty_iterable():
    nodes = [
        TextNode(content="Before"),
        ForNode(
            variable_name="item",
            iterable=["items"],
            body=[
                VariableNode(path=["item"]),
            ]
        ),
        TextNode(content="After")
    ]

    result = render(nodes=nodes, context={"items": []})
    assert result == "BeforeAfter"

def test_render_for_escapes_values():
    nodes = [
        ForNode(
            variable_name="item",
            iterable=["items"],
            body=[
                VariableNode(path=["item"]),
            ]
        )
    ]

    result = render(nodes=nodes, context={"items": ["<strong>Hello</strong>"]})
    assert result == "&lt;strong&gt;Hello&lt;/strong&gt;"

def test_render_for_does_not_leak_loop_variable():
    nodes = [
        ForNode(
            variable_name="item",
            iterable=["items"],
            body=[
                VariableNode(path=["item"]),
            ]
        ),
        TextNode(content=":"),
        VariableNode(path=["item"])
    ]

    result = render(nodes=nodes, context={"items": ["first", "second"], "item": "original"})

    assert result == "firstsecond:original"

def test_render_nested_for_nodes():
    nodes = [
        ForNode(
            variable_name="group",
            iterable=["groups"],
            body=[
                VariableNode(path=["group", "name"]),
                TextNode(content=":"),
                ForNode(
                    variable_name="member",
                    iterable=["group", "members"],
                    body=[
                        VariableNode(path=["member"]),
                        TextNode(content=",")
                    ]
                ),
                TextNode(content=";")
            ]
        )
    ]

    context = {
        "groups": [
            {"name": "Group1", "members": ["Alice", "Bob"]},
            {"name": "Group2", "members": ["Charlie"]}
        ]
    }

    result = render(nodes=nodes, context=context)
    assert result == "Group1:Alice,Bob,;Group2:Charlie,;"

def test_redner_for_rejects_non_iterable_value():
    nodes = [
        ForNode(
            variable_name="item",
            iterable=["items"],
            body=[
                VariableNode(path=["item"]),
            ]
        )
    ]

    with pytest.raises(TemplateRenderError) as error_info:
        render(nodes=nodes, context={"items": 42})

    assert str(error_info.value) == "Template value is not iterable: items"
