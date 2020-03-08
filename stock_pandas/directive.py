import re

from .common import (
    join_list,
    raise_if
)
from .command_presets import COMMAND_PRESETS

DEFAULT_ARG_VALUE = ''


def coerce_args(command_name, args, arg_settings):
    coerced = []
    length = len(args)

    max_args_length = len(arg_settings)

    if length > max_args_length:
        raise ValueError(
            f'command "{command_name}" accepts max {max_args_length} args, but got {length}' # noqa
        )

    for index, (default, setter) in enumerate(arg_settings):
        # Suppose command `foo` has two args
        # foo:,1 -> [default, '1']
        # foo    -> [default, default]
        arg = args[index] if index < length else DEFAULT_ARG_VALUE

        arg = default if arg == DEFAULT_ARG_VALUE else (
            # Setter could be optional
            setter(arg) if setter else arg
        )

        if arg is None:
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

    def apply_preset(self):
        if self.formula:
            return

        name = self.name
        preset = COMMAND_PRESETS.get(name)

        self.args = coerce_args(name, self.args, preset.args)
        self.formula = preset.formula

    def run(self, df, s: slice):
        return self.formula(df, s, *self.args)

    @staticmethod
    def from_string(name: str, strict: bool):
        name = name.strip()
        match = re.match(REGEX_COMMAND, name)

        if not match:
            return raise_if(
                strict,
                ValueError(f'invalid command `{name}`')
            )

        command, sub, args = match.group(1, 2, 3)
        if command not in COMMAND_PRESETS:
            return raise_if(
                strict,
                ValueError(f'unknown command "{command}"')
            )

        sub = sub[1:].strip() if sub else None
        args = [
            a.strip() for a in args[1:].split(ARGS_SEPARATOR)
        ] if args else []

        return Command(command, sub, args)


def parse_expression(expression, strict: bool):
    try:
        return float(expression)
    except ValueError:
        return Command.from_string(expression, strict)


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


REGEX_DIRECTIVE = r'^([a-z0-9.:,\s]+)(?:([=<>/\\]+)([\S\s]+))?$'


class Directive:
    def __init__(self, command, operator, expression):
        self.command = command
        self.operator = operator
        self.expression = expression

    def __str__(self):
        return f'{self.command}{self.operator}{self.expression}' \
            if self.operator else str(self.command)

    def apply_presets(self):
        self.command.apply_preset()

        if isinstance(self.expression, Command):
            self.expression.apply_preset()

    def run(self, df, s: slice):
        # TODO: support operator
        return self.command.run(df, s)

    @staticmethod
    def from_string(name: str, strict: bool):
        name = name.strip()
        match = re.match(REGEX_DIRECTIVE, name)

        if not match:
            return raise_if(
                strict,
                ValueError(f'invalid directive `{name}`')
            )

        raw_command, operator, expression = match.group(1, 2, 3)

        command = Command.from_string(raw_command, strict)
        if command is None:
            return

        if operator and operator not in OPERATORS:
            return raise_if(
                strict,
                ValueError(f'"{operator}" is an invalid operator')
            )

        if expression:
            expression = parse_expression(expression, strict)
            if expression is None:
                return

        return Directive(command, operator, expression)
