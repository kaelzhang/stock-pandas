from __future__ import annotations
from typing import (
    Optional,
    Generic,
    List,
    Union,
    # TypeVar
    # Tuple
)
from dataclasses import dataclass

from stock_pandas.exceptions import DirectiveValueError
from stock_pandas.common import (
    command_full_name,
    DEFAULT_ARG_VALUE
)

from .types import (
    Expression,
    Command,
    Operator
)
from .operator import (
    OperatorFormula,
    UnaryOperatorFormula,
    OF
)
from .tokenizer import Loc
from .command import (
    Context,
    ScalarNode
)


@dataclass(frozen=True, slots=True)
class ExpressionNode:
    loc: Loc
    left: ExpressionNodeTypes
    operator: Optional[OperatorNode[OperatorFormula]] = None
    right: Optional[ExpressionNodeTypes] = None

    # def create(
    #     self,
    #     context: Context
    # ) -> Directive:
    #     directive = (
    #         Directive(self.command.create(context))
    #         if self.operator is None
    #         else Directive(
    #             self.command.create(context),
    #             self.operator.create(context),
    #             self.expression.create(context)
    #         )
    #     )

    #     context.cache.set(str(directive), directive)

    #     return directive


@dataclass(frozen=True, slots=True)
class UnaryExpressionNode:
    loc: Loc
    operator: OperatorNode[UnaryOperatorFormula]
    expression: ExpressionNode

    def create(
        self,
        context: Context
    ) -> Expression:
        return Expression(self.operator.create(context), self.expression.create(context))


@dataclass(frozen=True, slots=True)
class CommandNode:
    loc: Loc
    name: ScalarNode
    args: List[ArgumentNode]
    series: List[SeriesArgumentNode]
    sub: Optional[ScalarNode] = None

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
                value = arg_node.create(context)
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


@dataclass(frozen=True, slots=True)
class ArgumentNode:
    loc: Loc
    value: ScalarNode

    def create(self, context: Context):
        return self.value.create(context)


@dataclass(frozen=True, slots=True)
class SeriesArgumentNode:
    loc: Loc
    value: ExpressionNodeTypes

    def create(self, context: Context):
        return self.value.create(context)


@dataclass(frozen=True, slots=True)
class OperatorNode(Generic[OF]):
    loc: Loc
    name: str
    formula: OF

    def create(self, _: Context) -> Operator:
        ...
        # return Operator(self.name, OPERATORS.get(self.name))


# @dataclass(frozen=True, slots=True)
# class UnaryOperatorNode:
#     loc: Loc
#     name: str
#     formula: UnaryOperatorFormula

#     def create(self, _: Context) -> UnaryOperator:
#         return UnaryOperator(self.name, UNARY_OPERATORS.get(self.name))


ExpressionNodeTypes = Union[
    ExpressionNode,
    UnaryExpressionNode,
    ScalarNode,
    CommandNode
]

# ArgumentValueNode = Union[DirectiveNode, ScalarNode]
# ExpressionNode = Union[ScalarNode, CommandNode]
# #
