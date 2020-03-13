# class SyntaxError(_StandardError):
#     msg: str
#     lineno: int
#     offset: Optional[int]
#     text: Optional[str]
#     filename: str


class DirectiveError(Exception):
    directive: str
    line: int
    column: int
    message: str

    def __str__(self):
        return f'directive "{self.directive}", line:{self.line}, column: {self.column}, message: {self.message}'  # noqa
        # TODO: code frame


class DirectiveSyntaxError(DirectiveError):
    def __init__(self, directive, message_template: str, token):
        line, column = token.loc

        self.directive = directive
        self.message = message_template.format(token.value)
        self.line = line
        self.column = column


def unexpected_token(directive, token):
    return DirectiveSyntaxError(directive, 'unexpected token "{}"', token)


class DirectiveValueError(DirectiveError):
    def __init__(self, directive, message, loc):
        self.directive = directive
        self.message = message

        line, column = loc
        self.line = line
        self.column = column
