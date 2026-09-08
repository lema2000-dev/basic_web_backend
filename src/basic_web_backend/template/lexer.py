from dataclasses import dataclass
from enum import Enum

from ..exceptions import TemplateSyntaxError, TemplateSyntaxError

class TokenType(Enum):
    TEXT = "TEXT"
    VARIABLE = "VARIABLE"
    STATEMENT = "STATEMENT"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

OPENING_DELIMITER = {
    "{{": ("}}", TokenType.VARIABLE, "Unclosed variable expression."),
    "{%": ("%}", TokenType.STATEMENT, "Unclosed statement block."),
    "{#": ("#}", None, "Unclosed template comment.")
}

def tokenize(source, template_name=None):
    tokens = []

    position = 0
    line = 1
    column = 1

    while position < len(source):
        opening_position, opening = (
            _find_next_opening(source, position)
        )
        if opening is None:
            remaining_text = source[position:]

            if remaining_text:
                tokens.append(
                    Token(
                        type=TokenType.TEXT,
                        value=remaining_text,
                        line=line,
                        column=column
                    )
                )
            break

        if opening_position > position:
            text = source[position:opening_position]
            tokens.append(
                Token(
                    type=TokenType.TEXT,
                    value=text,
                    line=line,
                    column=column
                )
            )
            line, column = _advance_position(text, line, column)

            position = opening_position

        token_line = line
        token_column = column

        closing, token_type, error_message = OPENING_DELIMITER[opening]
        closing_position = source.find(closing, position + len(opening))

        if closing_position == -1:
            raise TemplateSyntaxError(
                message=error_message,
                template_name=template_name,
                line=token_line,
                column=token_column
            )

        content_start = position + len(opening)
        content = source[content_start:closing_position]

        end_position = closing_position + len(closing)

        complete_section = source[position:end_position]

        if token_type is not None:
            tokens.append(
                Token(
                    type=token_type,
                    value=content.strip(),
                    line=token_line,
                    column=token_column
                )
            )

        line, column = _advance_position(text=complete_section, line=line, column=column)
        position = end_position

    return tokens

def _find_next_opening(source, start):
    next_position = None
    next_opening = None

    for opening in OPENING_DELIMITER:
        position = source.find(opening, start)

        if position == -1:
            continue

        if next_position is None or position < next_position:
            next_position = position
            next_opening = opening

    return next_position, next_opening

def _advance_position(text, line, column):
    newline_count = text.count("\n")

    if newline_count == 0:
        return line, column + len(text)

    line += newline_count

    text_after_last_newline = text.rsplit("\n", maxsplit=1)[1]
    column = len(text_after_last_newline) + 1

    return line, column

