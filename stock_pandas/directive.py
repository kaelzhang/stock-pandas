import re
import numpy as np

from .common import (
    raise_if,
    is_not_nan,
    split_and_balance,
    join_args
)
from .commands import COMMANDS
from .operators import OPERATORS

DEFAULT_ARG_VALUE = ''


def coerce_args(command_name, args, arg_settings):
    coerced = []
    length = len(args)

    max_args_length = len(arg_settings)

    if length > max_args_length:
        raise ValueError(
            f'command "{command_name}" accepts max {max_args_length} args, but got {length}'  # noqa
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


REGEX_COMMAND = \
    r'^([a-z]+)(\.[a-z]+)?\s*(:[a-z0-9-.\s(),:]+)?$'



class Command:
    def __init__(self, command, sub, args):
        self.name = command
        self.sub = sub
        self.args = args
        self.formula = None

    def __str__(self):
        name = self.full_name

        return f'{name}:{join_args(self.args)}' \
            if self.args else name

    @property
    def full_name(self):
        return f'{self.name}.{self.sub}' if self.sub else self.name


    def _get_preset(self):
        name = self.name
        preset = COMMANDS.get(name)

        sub = self.sub

        if self.sub is None:
            return preset

        sub_aliases_map = preset.sub_aliases_map
        subs_map = preset.subs_map

        # apply sub aliases
        sub = sub if sub_aliases_map is None else sub_aliases_map.get(sub, sub)
        self.sub = sub

        # macd.dif -> macd
        if sub is None:
            return preset

        if subs_map is None:
            raise ValueError(f'command "{name}" has no sub commands')

        if sub not in subs_map:
            raise ValueError(
                f'unknown sub command "{sub}" for command "{name}"'
            )

        return subs_map.get(sub)

    def apply_preset(self):
        if self.formula:
            return

        preset = self._get_preset()

        self.args = coerce_args(self.full_name, self.args, preset.args)
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
        if command not in COMMANDS:
            return raise_if(
                strict,
                ValueError(f'unknown command "{command}"')
            )

        preset = COMMANDS.get(command)

        sub = sub[1:].strip() if sub else None

        if preset.formula is None and sub is None:
            return raise_if(
                strict,
                ValueError(
                    f'sub command should be specified for command "{command}"'
                )
            )

        args = split_and_balance(args[1:], strict) if args else []

        if args is None:
            return

        return Command(command, sub, args)


class Operator:
    def __init__(self, name, formula):
        self.name = name
        self.formula = formula

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(name: str, strict: bool):
        if name not in OPERATORS:
            return raise_if(
                strict,
                ValueError(f'"{name}" is an invalid operator')
            )

        formula = OPERATORS.get(name)
        return Operator(name, formula)


def parse_expression(expression, strict: bool):
    try:
        return float(expression)
    except ValueError:
        return Command.from_string(expression, strict)


REGEX_DIRECTIVE = r'^([a-z0-9-.:,\s()]+)(?:([=<>/\\]+)([\S\s]+))?$'


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
        left, period_left = self.command.run(df, s)

        if not self.operator:
            return left, period_left

        expr = self.expression

        right, period_right = expr.run(df, s) if isinstance(expr, Command) \
            else (expr, 0)

        operated = self.operator.formula(left, right)

        # Plan.A: `np.nan` makes non-sense, so mark them all as False
        # or Plan.B: mark as `np.nan` ?
        # Plan.A has better compatibility,
        #   and `operated` is often used as condition indexer,
        #   so it must be of bool type
        operated = operated & is_not_nan(left) & is_not_nan(right)

        return operated, max(period_left, period_right)

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

        if operator:
            operator = Operator.from_string(operator, strict)
            if operator is None:
                return

        if expression:
            expression = parse_expression(expression, strict)
            if expression is None:
                return

        return Directive(command, operator, expression)
