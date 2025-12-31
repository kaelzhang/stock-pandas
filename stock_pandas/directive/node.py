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
    DEFAULT_ARG_VALUE
)

from .types import (
    Directive,
    Command,
    Operator,
    Argument
)
from .operator import OPERATORS
from .tokenizer import Loc
from .command import (
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
            Directive(self.command.create(context))
            if self.operator is None
            else Directive(
                self.command.create(context),
                self.operator.create(context),
                self.expression.create(context)
            )
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

            is_directive = False

            if index < args_length:
                arg_node = args[index]
                loc = arg_node.loc
                value = arg_node.value.create(context)
                is_directive = isinstance(value, Directive)
            else:
                # If the arg does not exist, use the command loc
                loc = context.loc
                value = DEFAULT_ARG_VALUE

            if value == DEFAULT_ARG_VALUE:
                value = default

            # Setter could be optional
            elif (
                setter is not None
                and not is_directive
            ):
                try:
                    value = setter(value)
                except ValueError as e:
                    raise DirectiveValueError(
                        context.input,
                        str(e),
                        loc
                    )

            if value is None:
                raise DirectiveValueError(
                    context.input,
                    f'args[{index}] is required for command "{command_name}"',
                    loc
                )

            coerced_args.append(
                Argument(value, is_directive)
            )

        return Command(
            command_full_name(main_name, sub_name),
            coerced_args,
            preset.formula
        )


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
