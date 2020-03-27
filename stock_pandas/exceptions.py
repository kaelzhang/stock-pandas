import re

REGEX_CARRIAGE_RETURN = re.compile(r'\r|\n', re.A)
CR = '\n'
WHITESPACE = ' '


class DirectiveError(Exception):
    directive: str
    line: int
    column: int
    message: str

    def __str__(self) -> str:
        # The column of Python SyntaxError is buggy
        # So, do not use Python built-in SyntaxError.

        splitted = REGEX_CARRIAGE_RETURN.split(self.directive)
        line = self.line

        formatted = CR.join([
            f'>  {code_line}' if index == line - 1 else f'   {code_line}'
            for index, code_line in enumerate(splitted)
        ])

        return f'''File "<string>", line {self.line}, column {self.column}
{formatted}
   {WHITESPACE * (self.column - 1)}^
DirectiveSyntaxError: {self.message}'''


class DirectiveSyntaxError(DirectiveError):
    def __init__(self, directive, message_template: str, token) -> None:
        line, column = token.loc

        self.directive = directive
        self.message = message_template.format(token.value)
        self.line = line
        self.column = column


def unexpected_token(directive, token) -> DirectiveSyntaxError:
    return DirectiveSyntaxError(directive, 'unexpected token "{}"', token)


class DirectiveValueError(DirectiveError):
    def __init__(self, directive, message, loc) -> None:
        self.directive = directive
        self.message = message

        line, column = loc
        self.line = line
        self.column = column
