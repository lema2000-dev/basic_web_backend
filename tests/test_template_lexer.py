import pytest

from basic_web_backend.exceptions import (
    TemplateSyntaxError
)
from basic_web_backend.template.lexer import (
    Token,
    TokenType,
    tokenize
)

def test_tokenize_plain_text():
    tokens = tokenize("<h1>Hello, World!</h1>")

    assert tokens == [
        Token(
            type=TokenType.TEXT,
            value="<h1>Hello, World!</h1>",
            line=1,
            column=1
        )
    ]

def test_tokenize_variable():
    tokens = tokenize("<h1>Hello, {{ username }}!</h1>")

    assert tokens == [
        Token(
            type=TokenType.TEXT,
            value="<h1>Hello, ",
            line=1,
            column=1
        ),
        Token(
            type=TokenType.VARIABLE,
            value="username",
            line=1,
            column=12
        ),
        Token(
            type=TokenType.TEXT,
            value="!</h1>",
            line=1,
            column=26
        )
    ]

def test_tokenize_statment():
    tokens = tokenize(
        "{% if authenticated %}Welcome{% endif %}"
    )

    assert tokens == [
        Token(
            type=TokenType.STATEMENT,
            value="if authenticated",
            line=1,
            column=1
        ),
        Token(
            type=TokenType.TEXT,
            value="Welcome",
            line=1,
            column=23
        ),
        Token(
            type=TokenType.STATEMENT,
            value="endif",
            line=1,
            column=30
        )
    ]

def test_tokenize_ignore_comments():
    tokens = tokenize(
        "Hello{# This is a comment #}World!"
    )

    assert tokens == [
        Token(
            type=TokenType.TEXT,
            value="Hello",
            line=1,
            column=1
        ),
        Token(
            type=TokenType.TEXT,
            value="World!",
            line=1,
            column=29
        )
    ]

def test_tokenize_tracks_line_and_column():
    template = "<h1>Profile</h1>\n    <p>{{ user.name }}</p>"
    tokens = tokenize(template)
    variable_token = tokens[1]

    assert variable_token.type == TokenType.VARIABLE
    assert variable_token.value == "user.name"
    assert variable_token.line == 2
    assert variable_token.column == 8

def test_tokenize_rejects_unclosed_variable():
    with pytest.raises(TemplateSyntaxError) as error_info:
        tokenize("<h1>{{ username </h1>", 
            template_name="profile.html"
        )

    error = error_info.value

    assert error.template_name == "profile.html"
    assert error.line == 1
    assert error.column == 5
    assert error.message == "Unclosed variable expression."

def test_tokenize_rejects_unclosed_statement():
    with pytest.raises(TemplateSyntaxError) as error_info:
        tokenize("{% if authenticated", 
            template_name="profile.html"
        )

    assert error_info.value.message == "Unclosed statement block."

def test_tokenize_rejects_unclosed_comment():
    with pytest.raises(TemplateSyntaxError) as error_info:
        tokenize("{# unfinished comment", 
            template_name="profile.html"
        )

    assert error_info.value.message == "Unclosed template comment."