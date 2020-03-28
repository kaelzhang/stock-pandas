from typing import (
    Tuple,
    Union,
    List,
    Optional,
    overload
)

from .types import (
    Directive,
    Command,
    Argument,
    Operator
)

from .operators import OPERATORS
from .parser import (
    Node,
    NotNode,
    Loc
)

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

    def __init__(
        self,
        input: str,
        loc: Loc,
        cache
    ):
        self.input = input
        self.loc = loc
        self.cache = cache


def create_directive(
    context: Context,
    command,
    operator,
    expression
):
    directive = Directive(command[0]) if operator is None else Directive(
        command[0], operator[0], expression[0]
    )

    context.cache.set(str(directive), directive)

    return directive


def create_command(context, name, sub, args) -> Command:
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
    raw_name: Tuple[str, Loc],
    raw_sub: Optional[Tuple[str, Loc]]
) -> Tuple[str, Optional[str], CommandPreset]:
    """Gets the sanitized command infos, including:
    - command name,
    - optional sub command name
    - and command preset
    """

    name, name_loc = raw_name
    sub, sub_loc = raw_sub if raw_sub is not None else NONE_TUPLE

    if name not in COMMANDS:
        raise DirectiveValueError(
            context.input,
            f'unknown command "{name}"',
            name_loc
        )

    main_command_preset, subs_map, sub_aliases_map = COMMANDS[name]

    # applies sub aliases, and get the real sub name
    if sub is not None and sub_aliases_map is not None:
        real_sub = sub_aliases_map.get(sub, sub)
    else:
        real_sub = sub

    if real_sub is not None:
        if subs_map is None:
            raise DirectiveValueError(
                context.input,
                f'command "{name}" has no sub commands',
                sub_loc
            )

        if real_sub not in subs_map:
            raise DirectiveValueError(
                context.input,
                f'unknown sub command "{sub}" for command "{name}"',
                sub_loc
            )

        return name, real_sub, subs_map[real_sub]

    if main_command_preset is None:
        raise DirectiveValueError(
            context.input,
            f'sub command should be specified for command "{name}"',
            name_loc
        )

    return name, None, main_command_preset


def create_operator(_, operator: str) -> Operator:
    # The operator has already been validated by parser
    return Operator(operator, OPERATORS.get(operator))  # type: ignore


def create_argument(_, arg) -> Argument:
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


FactoryReturnType = Tuple[
    Union[
        Directive,
        Command,
        Argument,
        Operator
    ],
    Loc
]


@overload
def create_by_node(
    node: List[Union[Node, NotNode]],
    input: str,
    cache
) -> List[Union[FactoryReturnType, NotNode]]:
    ...  # pragma: no cover


@overload
def create_by_node(
    node: NotNode,
    input: str,
    cache
) -> NotNode:
    ...  # pragma: no cover


def create_by_node(
    node: Node,
    input: str,
    cache
) -> FactoryReturnType:
    if isinstance(node, list):
        return [
            create_by_node(arg, input, cache) for arg in node  # type: ignore
        ]

    if not isinstance(node, Node):
        return node  # type: ignore

    factory = FACTORY.get(node.label)
    loc = node.loc

    context = Context(
        input,
        loc,
        cache
    )

    args = [
        create_by_node(arg, input, cache) for arg in node.data  # type: ignore
    ]

    # For node, we return the instance and loc
    return factory(context, *args), loc
