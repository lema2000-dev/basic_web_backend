from basic_web_backend.template.evaluator import render
from basic_web_backend.template.lexer import tokenize
from basic_web_backend.template.parser import parse

def render_source(source, context=None, autoescape=True, template_name=None):
    tokens = tokenize(source, template_name=template_name)
    nodes = parse(tokens, template_name=template_name)
    return render(nodes, context=context, autoescape=autoescape, template_name=template_name)

def test_complete_template_pipeline():
    source = (
        "<h1>Hello, {{ user.name }}!</h1>"
        "{# This is a comment is removed #}"
        "{% if user.active %}"
        "<ul>"
        "{% for role in user.roles %}"
        "<li>{{ role }}</li>"
        "{% endfor %}"
        "</ul>"
        "{% else %}"
        "<p>Inactive user</p>"
        "{% endif %}"
    )

    result = render_source(
        source=source,
        context={
            "user": {
                "name": "<Martin>",
                "active": True,
                "roles": ["Developer", "Tester"]
            }
        },
        template_name="profile.html"
    )

    assert result == (
        "<h1>Hello, &lt;Martin&gt;!</h1>"
        "<ul>"
        "<li>Developer</li>"
        "<li>Tester</li>"
        "</ul>"
    )

def test_pipeline_skips_inactive_branch():
    source = (
        "{% if user.active %}"
        "{% for role in user.roles %}"
        "{{ role }}"
        "{% endfor %}"
        "{% else %}"
        "<p>Inactive user</p>"
        "{% endif %}"
    )

    result = render_source(
        source=source,
        context={
            "user": {
                "active": False,
            },
        },
    )

    assert result == (
        "<p>Inactive user</p>"
    )

def test_pipeline_can_disable_autoescape():
    source = (
        "<div>{{ content }}</div>"
    )

    result = render_source(
        source=source,
        context={
            "content": (
                "<strong>Hello</strong>"
            ),
        },
        autoescape=False,
    )

    assert result == (
        "<div>"
        "<strong>Hello</strong>"
        "</div>"
    )

