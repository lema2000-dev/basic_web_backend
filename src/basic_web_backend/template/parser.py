import re

from ..exceptions import TemplateSyntaxError
from .lexer import TokenType
from .nodes import TextNode, VariableNode, IfNode, ForNode

VARIABLE_PATH_PATTERN = re.compile(
    r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*"
)

FOR_STATEMENT_PATTERN = re.compile(
    r"for\s+(?P<variable>[A-Za-z_]\w*)"
    r"\s+in\s+(?P<iterable>.+)"
)

def parse(tokens, template_name=None):
    parser = Parser(tokens, template_name)
    return parser.parse()

class Parser:
    def __init__(self, tokens, template_name=None):
        self.tokens = list(tokens)
        self.template_name = template_name
        self.position = 0

    def parse(self):
        nodes, closing_statment = self._parse_nodes(stop_statements=set())

        if closing_statment is not None:
            token = self.tokens[self.position]

            self._raise_unexpected_statment(token)

        return nodes

    def _parse_nodes(self, stop_statements):
        nodes = []

        while self.position < len(self.tokens):
            token = self.tokens[self.position]

            if token.type == TokenType.TEXT:
                nodes.append(
                    TextNode(
                        content=token.value,
                        line=token.line,
                        column=token.column
                    )
                )
                self.position += 1
                continue

            if token.type == TokenType.VARIABLE:
                nodes.append(self._parse_variable(token))
                self.position += 1
                continue

            if token.type == TokenType.STATEMENT:
                statement = token.value

                if statement in stop_statements:
                    return nodes, statement

                keyword = self._get_keyword(statement)

                if keyword == "if":
                    nodes.append(self._parse_if(opening_token=token))
                    continue

                if keyword == "for":
                    nodes.append(self._parse_for(opening_token=token))
                    continue

                if statement in {"endif", "else", "endfor"}:
                    self._raise_unexpected_statment(token)

                self._raise_syntax_error(
                    message=f"Unknown template statement: {statement}",
                    token=token
                )

            self._raise_syntax_error(
                message=f"Unkonwn template token type: {token.type}",
                token=token
            )

        return nodes, None

    def _parse_variable(self, token):
        path = self._parse_variable_path(expression=token.value, token=token, empty_message="Variable expression cannot be empty.")

        return VariableNode(
            path=path,
            line=token.line,
            column=token.column
        )

    def _parse_if(self, opening_token):
        parts = opening_token.value.split(maxsplit=1)

        if len(parts) == 1:
            self._raise_syntax_error(
                message="If statement requires a condition.",
                token=opening_token
            )

        condition_expression = parts[1].strip()

        condition = self._parse_variable_path(
            expression=condition_expression,
            token=opening_token,
            empty_message="If statement requires a condition."
        )

        self.position += 1

        body, closing_statement = self._parse_nodes(stop_statements={"else", "endif"})

        if closing_statement is None:
            self._raise_syntax_error(
                message="Missing endif statement.",
                token=opening_token
            )

        else_body = []

        if closing_statement == "else":
            self.position += 1

            else_body, closing_statement = self._parse_nodes(stop_statements={"endif"})

            if closing_statement is None:
                self._raise_syntax_error(
                    message="Missing endif statement.",
                    token=opening_token
                )

        self.position += 1

        return IfNode(
            condition=condition,
            body=body,
            else_body=else_body,
            line=opening_token.line,
            column=opening_token.column
        )

    def _parse_variable_path(self, expression, token, empty_message):
        if not expression:
            self._raise_syntax_error(
                message=empty_message,
                token=token
            )

        if VARIABLE_PATH_PATTERN.fullmatch(expression) is None:
            self._raise_syntax_error(
                message=f"Invalid variable expression: {expression}",
                token=token
            )

        return expression.split(".")

    def _get_keyword(self, statement):
        parts = statement.split(maxsplit=1)
        if not parts:
            return ""

        return parts[0]

    def _raise_unexpected_statment(self, token):
        self._raise_syntax_error(
            message=f"Unexpected {token.value} statement.",
            token=token
        )

    def _raise_syntax_error(self, message, token):
        raise TemplateSyntaxError(
            message=message,
            template_name=self.template_name,
            line=token.line,
            column=token.column
        )

    def _parse_for(self, opening_token):
        match = FOR_STATEMENT_PATTERN.fullmatch(opening_token.value)

        if match is None:
            self._raise_syntax_error(
                message=f"Invalid for statement. Expected format: 'for <variable> in <iterable>'.",
                token=opening_token
            )

        variable_name = match.group("variable")

        iterable_expression = match.group("iterable").strip()

        iterable = self._parse_variable_path(
            expression=iterable_expression,
            token=opening_token,
            empty_message="Invalid for statement. Expected format: 'for <variable> in <iterable>'."
        )

        self.position += 1

        body, closing_statement = self._parse_nodes(stop_statements={"endfor"})

        if closing_statement is None:
            self._raise_syntax_error(
                message="Missing endfor statement.",
                token=opening_token
            )

        self.position += 1

        return ForNode(
            variable_name=variable_name,
            iterable=iterable,
            body=body,
            line=opening_token.line,
            column=opening_token.column
        )