from typing import (
    Tuple
)

from .types import (
    Directive,
    Command,
    Argument,
    Operator
)

from .operators import OPERATORS
from .parser import Node

from stock_pandas.commands import (
    COMMANDS,
    CommandPreset
)

from stock_pandas.exceptions import DirectiveValueError

from stock_pandas.common import (
    command_full_name,
    NONE_TUPLE,
    DEFAULT_ARG_VALUE,

    TYPE_DIRECTIVE,
    TYPE_COMMAND,
    TYPE_OPERATOR,
    TYPE_ARGUMENT,
    TYPE_SCALAR
)


class Context:
    __slots__ = (
        'input',
        'loc',
        'cache'
    )

    def __init__(self, input, loc, cache):
        self.input = input
        self.loc = loc
        self.cache = cache


def create_directive(
    context,
    command,
    operator,
    expression
):
    directive = Directive(command[0]) if operator is None else Directive(
        command[0], operator[0], expression[0]
    )

    context.cache.set(str(directive), directive)

    return directive


def create_command(context, name, sub, args):
    name, sub, preset = process_command_name(context, name, sub)

    preset_args = preset.args
    max_lenth = len(preset_args)
    args_length = len(args)

    command_name = command_full_name(name, sub)

    if args_length > max_lenth:
        msg = f'command "{command_name}" accepts max {max_lenth} args'

        raise DirectiveValueError(
            context.input,
            msg,
            context.loc
        )

    coerced_args = []

    for index, (default, setter) in enumerate(preset.args):
        if index < args_length:
            argument, loc = args[index]
            arg = argument.value
        else:
            # If the arg does not exist, use the command loc
            loc = context.loc
            arg = DEFAULT_ARG_VALUE
            argument = Argument(arg)

        if arg == DEFAULT_ARG_VALUE:
            arg = default

        # Setter could be optional
        elif setter:
            try:
                arg = setter(arg)
            except ValueError as e:
                raise DirectiveValueError(
                    context.input,
                    str(e),
                    loc
                )

        if arg is None:
            raise DirectiveValueError(
                context.input,
                f'args[{index}] is required for command "{command_name}"',
                loc
            )

        argument.value = arg

        coerced_args.append(argument)

    return Command(name, sub, coerced_args, preset.formula)


def process_command_name(
    context,
    name,
    sub
) -> Tuple[int, int, CommandPreset]:
    name, name_loc = name
    sub, sub_loc = sub if sub else NONE_TUPLE

    preset = COMMANDS.get(name, None)

    if not preset:
        raise DirectiveValueError(
            context.input,
            f'unknown command "{name}"',
            name_loc
        )

    if sub is None:
        if preset.formula is None:
            raise DirectiveValueError(
                context.input,
                f'sub command should be specified for command "{name}"',
                name_loc
            )

        return name, sub, preset

    sub_aliases_map = preset.sub_aliases_map
    subs_map = preset.subs_map

    # apply sub aliases
    sub = sub if sub_aliases_map is None else sub_aliases_map.get(sub, sub)

    # macd.dif -> macd
    if sub is None:
        return name, sub, preset

    if subs_map is None:
        raise DirectiveValueError(
            context.input,
            f'command "{name}" has no sub commands',
            sub_loc
        )

    if sub not in subs_map:
        raise DirectiveValueError(
            context.input,
            f'unknown sub command "{sub}" for command "{name}"',
            sub_loc
        )

    return name, sub, subs_map.get(sub)


def create_operator(_, operator):
    # The operator has already been validated by parser
    return Operator(operator, OPERATORS.get(operator))


def create_argument(_, arg):
    arg = arg[0]

    if isinstance(arg, Directive):
        return Argument(str(arg), True)

    return Argument(arg)


FACTORY = {
    TYPE_DIRECTIVE: create_directive,
    TYPE_COMMAND: create_command,
    TYPE_OPERATOR: create_operator,
    TYPE_ARGUMENT: create_argument,
    TYPE_SCALAR: lambda _, value: value
}


def create_by_node(
    node,
    input: str,
    cache
):
    if isinstance(node, list):
        return [
            create_by_node(arg, input, cache) for arg in node
        ]

    if not isinstance(node, Node):
        return node

    factory = FACTORY.get(node.label)
    loc = node.loc

    context = Context(
        input,
        loc,
        cache
    )

    args = [
        create_by_node(arg, input, cache) for arg in node.data
    ]

    # For node, we return the instance and loc
    return factory(context, *args), loc
