from basic_web_backend.template.nodes import (
    ForNode,
    IfNode,
    TemplateNode,
    TextNode,
    VariableNode,
)

def test_text_node_stores_content():
    node = TextNode(
        content="<h1>Hello, World!</h1>",
        line = 1,
        column = 1
    )

    assert isinstance(node, TemplateNode)
    assert node.content == "<h1>Hello, World!</h1>"
    assert node.line == 1
    assert node.column == 1

def test_variable_node_stores_variable_path():
    node = VariableNode(
        path=["user", "name"],
        line=3,
        column=1
    )

    assert isinstance(node, TemplateNode)
    assert node.path == ["user", "name"]
    assert node.line == 3
    assert node.column == 1

def test_if_node_stores_branches():
    true_node = TextNode(
        content="<p>True branch</p>"
    )
    false_node = TextNode(
        content="<p>False branch</p>"
    )

    node = IfNode(
        condition=["user", "authenticated"],
        body=[true_node],
        else_body=[false_node],
        line=2,
        column=1
    )

    assert isinstance(node, TemplateNode)
    assert node.condition == ["user", "authenticated"]
    assert node.body == [true_node]
    assert node.else_body == [false_node]
    assert node.line == 2
    assert node.column == 1

def test_for_node_stores_loop_info():
    child_node = VariableNode(
        path=["item", "name"]
    )

    node = ForNode(
        variable_name="item",
        iterable=["items"],
        body=[child_node],
        line=5,
        column=1
    )

    assert isinstance(node, TemplateNode)
    assert node.variable_name == "item"
    assert node.iterable == ["items"]
    assert node.body == [child_node]
    assert node.line == 5
    assert node.column == 1

def test_node_position_defaults_to_frst_character():
    node = TextNode(
        content="<p>Default position</p>"
    )

    assert node.line == 1
    assert node.column == 1

def test_if_nodes_have_idependent_branches():
    first = IfNode(
        condition=["first_condition"]
    )
    second = IfNode(
        condition=["second_condition"]
    )

    first.body.append(TextNode(content="<p>First branch</p>"))

    assert len(first.body) == 1
    assert second.body == []
    assert first.body is not second.body
