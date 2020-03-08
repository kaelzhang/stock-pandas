import re

from .common import (
    join_list,
    memoize
)

DEFAULT_ARG_VALUE = ''

def coerce_args(command_name, args, arg_settings):
    coerced = []
    length = len(args)

    max_args_length = len(arg_settings)

    if length > max_args_length:
        raise ValueError(
            f'command "{command_name}" accepts max {max_args_length} args, but got {length}')

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
        self.formula = None

    def __str__(self):
        name = f'{self.name}.{self.sub}' if self.sub else self.name

        return f'{name}:{join_list(self.args, ARGS_SEPARATOR)}' \
            if self.args else name

    def apply_preset(self, preset):
        self.args = coerce_args(self.name, self.args, preset.args)
        self.formula = preset.formula

    def run(self, df, s: slice):
        return self.formula(df, s, *self.args)

    @staticmethod
    @memoize
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

def check_and_apply_command_preset(command, presets):
    if command.formula:
        return

    name = command.name

    command_preset = presets.get(name, None)

    if not command_preset:
        raise ValueError(f'command "{name}" is not supported')

    command.apply_preset(command_preset)

REGEX_DIRECTIVE = r'^([a-z0-9.:,\s]+)(?:([=<>/\\]+)([\S\s]+))?$'

class Directive:
    def __init__(self, command, operator, expression):
        self.command = command
        self.operator = operator
        self.expression = expression

    def __str__(self):
        return f'{self.command}{self.operator}{self.expression}' \
            if self.operator else str(self.command)

    def apply_presets(self, presets):
        check_and_apply_command_preset(self.command, presets)

        if type(self.expression) is Command:
            check_and_apply_command_preset(self.expression, presets)

    def run(self, df, s: slice):
        # TODO: support operator
        return self.command.run(df, s)

    @staticmethod
    def from_string(name: str):
        name = name.strip()
        match = re.match(REGEX_DIRECTIVE, name)

        if not match:
            raise ValueError(f'invalid column name `{name}`')

        raw_command, operator, expression = match.group(1, 2, 3)

        if operator:
            check_operator(operator)

        return Directive(
            Command.from_string(raw_command),
            operator,
            parse_expression(expression)
        )
