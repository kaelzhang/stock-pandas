import re

from .directive.tokenizer import (
    Loc, Token
)


REGEX_CARRIAGE_RETURN = re.compile(r'\r|\n', re.A)
CR = '\n'
WHITESPACE = ' '


def format_error_message(
    directive: str,
    name: str,
    line: int,
    column: int,
    message: str
) -> str:
    splitted = REGEX_CARRIAGE_RETURN.split(directive)

    formatted = CR.join([
        f'>  {code_line}' if index == line - 1 else f'   {code_line}'
        for index, code_line in enumerate(splitted)
    ])
    return f'''File "<string>", line {line}, column {column}
{formatted}
   {WHITESPACE * (column - 1)}^
{name}: {message}'''



class FormatMessageMixin:
    directive: str
    line: int
    column: int
    message: str
    name: str = 'DirectiveSyntaxError'

    def __str__(self) -> str:
        # The column of Python SyntaxError is buggy
        # So, do not use Python built-in SyntaxError.

        return format_error_message(
            self.directive,
            self.name,
            self.line,
            self.column,
            self.message
        )


class DirectiveError(FormatMessageMixin, Exception): ...


class DirectiveSyntaxError(DirectiveError):
    def __init__(
        self,
        directive: str,
        message_template: str,
        token: Token
    ) -> None:
        line, column = token.loc

        self.directive = directive
        self.message = message_template.format(token.value)
        self.line = line
        self.column = column


def unexpected_token(directive: str, token: Token) -> DirectiveSyntaxError:
    return DirectiveSyntaxError(directive, 'unexpected token "{}"', token)


class DirectiveValueError(DirectiveError):
    name: str = 'DirectiveValueError'

    def __init__(self, directive: str, message: str, loc: Loc) -> None:
        self.directive = directive
        self.message = message

        line, column = loc
        self.line = line
        self.column = column


class DirectiveNonSenseWarning(FormatMessageMixin, RuntimeWarning):
    name: str = 'DirectiveNonSenseWarning'

    def __init__(self, directive: str, loc: Loc) -> None:
        self.directive = directive
        self.message = 'it is a non-sense directive without any command'

        line, column = loc
        self.line = line
        self.column = column
