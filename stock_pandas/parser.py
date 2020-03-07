import re

from .utils import join_list

DEFAULT_ARG_VALUE = ''

def coerce_args(command_name, args, arg_settings):
    coerced = []
    length = len(args)

    for index, (default, setter) in enumerate(arg_settings):
        # Suppose command `foo` has two args
        # foo:,1 -> [default, '1']
        # foo    -> [default, default]
        arg = args[index] if index < length else DEFAULT_ARG_VALUE

        arg = default if arg == DEFAULT_ARG_VALUE else (
            # Setter could be optional
            setter(arg) if setter else arg
        )

        if arg == None:
            raise ValueError(
                f'args[{index}] is required for command "{command_name}"'
            )

        coerced.append(arg)

    return coerced

REGEX_COMMAND = r'^([a-z]+)(\.[a-z]+)?\s*(:[a-z0-9-.\s]+(?:,[a-z0-9-.\s]+)*)?$'
ARGS_SEPARATOR = ','

class Command:
    def __init__(self, command, sub, args):
        self.name = command
        self.sub = sub
        self.args = args

    def __str__(self):
        name = f'{self.name}.{self.sub}' if self.sub else self.name

        return f'{name}:{join_list(self.args, ARGS_SEPARATOR)}' \
            if self.args else name

    def apply_args_settings(self, args_settings):
        self.args = coerce_args(self.name, self.args, args_settings)

    @staticmethod
    def from_string(name: str):
        name = name.strip()
        match = re.match(REGEX_COMMAND, name)

        if not match:
            raise ValueError(f'invalid command `{name}`')

        command, sub, args = match.group(1, 2, 3)
        sub = sub[1:].strip() if sub else None
        args = [
            a.strip() for a in args[1:].split(ARGS_SEPARATOR)
        ] if args else []

        return Command(command, sub, args)


def parse_expression(expression):
    if not expression:
        return

    try:
        return float(expression)
    except ValueError:
        return Command.from_string(expression)

OPERATORS = [
    '/',
    '\\',
    '<',
    '<=',
    '==',
    '>=',
    '>',
    '><'
]

def check_operator(operator: str):
    if operator in OPERATORS:
        return

    raise ValueError(f'"{operator}" is an invalid operator')

REGEX_COLUMN_NAME = r'^([a-z0-9.:,\s]+)(?:([=<>/\\]+)([\S\s]+))?$'

class ColumnName:
    def __init__(self, command, operator, expression):
        self.command = command
        self.operator = operator
        self.expression = expression

    def __str__(self):
        return f'{self.command}{self.operator}{self.expression}' \
            if self.operator else str(self.command)

    @staticmethod
    def from_string(name: str):
        name = name.strip()
        match = re.match(REGEX_COLUMN_NAME, name)

        if not match:
            raise ValueError(f'invalid column name `{name}`')

        raw_command, operator, expression = match.group(1, 2, 3)

        if operator:
            check_operator(operator)

        return ColumnName(
            Command.from_string(raw_command),
            operator,
            parse_expression(expression)
        )
