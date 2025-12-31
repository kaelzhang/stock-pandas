from __future__ import annotations
from typing import (
    Optional,
    Union,
    List,
    # Tuple
)
from dataclasses import dataclass

from stock_pandas.exceptions import DirectiveValueError
from stock_pandas.common import (
    command_full_name,
)

from .types import (
    Directive,
    Command,
    Operator
)
from .operator import OPERATORS
from .tokenizer import Loc
from .command import (
    # CommandPreset,
    Context,
    ScalarNode
)


# class MetaNode:
#     """
#     The meta node which is used to distinguish the type of Node and RootNode
#     """

#     # __slots__ = ('label', 'data', 'loc')

#     # label: int
#     # data: NodeData
#     loc: Loc

#     # def __init__(self, t, data, loc):
#     #     self.label = t
#     #     self.data = data
#     #     self.loc = loc


# class Node(MetaNode):
#     ...


# class RootNode(MetaNode):
#     @classmethod
#     def from_node(cls, node: MetaNode) -> 'RootNode':
#         return cls(
#             node.label,
#             node.data,
#             node.loc
#         )


@dataclass
class DirectiveNode:
    command: CommandNode
    operator: Optional[OperatorNode] = None
    expression: Optional[ExpressionNode] = None
    loc: Loc

    def create(
        self,
        context: Context
    ) -> Directive:
        directive = (
            Directive(self.command)
            if self.operator is None
            else Directive(self.command, self.operator, self.expression)
        )

        context.cache.set(str(directive), directive)

        return directive


@dataclass
class CommandNode:
    name: ScalarNode
    sub: Optional[ScalarNode] = None
    args: List[ArgumentNode]
    loc: Loc

    def create(
        self,
        context: Context
    ) -> Command:
        main_name = self.name.value
        commands = context.commands
        command_def = commands.get(main_name)

        if command_def is None:
            raise DirectiveValueError(
                context.input,
                f'unknown command "{main_name}"',
                self.name.loc
            )

        preset, sub_name = command_def.get_preset(self.name, self.sub, context)

        preset_args = preset.args
        args = self.args


        max_length = len(preset_args)
        args_length = len(args)

        command_name = command_full_name(main_name, sub_name)

        if args_length > max_length:
            raise DirectiveValueError(
                context.input,
                f'command "{command_name}" accepts max {max_length} args',
                context.loc
            )

        coerced_args = []

        for index, arg_def in enumerate(preset_args):
            default = arg_def.default
            setter = arg_def.coerce

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


@dataclass
class ArgumentNode:
    value: ArgumentValueNode
    loc: Loc

    def create(self, context: Context):
        return self.value.create(context)


@dataclass
class OperatorNode:
    operator: str
    loc: Loc

    def create(self, _: Context) -> Operator:
        return Operator(self.operator, OPERATORS.get(self.operator))


ArgumentValueNode = Union[DirectiveNode, ScalarNode]
ExpressionNode = Union[ScalarNode, CommandNode]
