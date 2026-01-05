from __future__ import annotations
from typing import (
    Optional,
    Generic,
    List,
    Union
)
from dataclasses import dataclass

from stock_pandas.exceptions import DirectiveValueError
from stock_pandas.common import (
    command_full_name
)

from .types import (
    Expression,
    UnaryExpression,
    Command,
    Operator,
    PrimativeType,
    CommandArgInputType,
    CommandSeriesType,
    NumberType
)
from .operator import (
    OperatorFormula,
    UnaryOperatorFormula,
    OF
)
from .tokenizer import Loc
from .command import (
    Context,
    ScalarNode,
    CommandPreset,
    column,
    lookback_zero
)


@dataclass(frozen=True, slots=True)
class ExpressionNode:
    loc: Loc
    left: ExpressionNodeTypes
    operator: OperatorNode[OperatorFormula]
    right: ExpressionNodeTypes

    def create(
        self,
        context: Context
    ) -> Expression:
        return Expression(
            operator=self.operator.create(context),
            left=self.left.create(context),
            right=self.right.create(context)
        )


@dataclass(frozen=True, slots=True)
class UnaryExpressionNode:
    loc: Loc
    operator: OperatorNode[UnaryOperatorFormula]
    expression: ExpressionNode

    def create(
        self,
        context: Context
    ) -> UnaryExpression:
        return UnaryExpression(
            operator=self.operator.create(context),
            expression=self.expression.create(context)
        )


@dataclass(frozen=True, slots=True)
class CommandNode:
    loc: Loc
    name: ScalarNode[str]
    args: List[ArgumentNode]
    series: List[SeriesArgumentNode]
    sub: Optional[ScalarNode[str]] = None

    def _empty_command(self, _: Context) -> Optional[Command]:
        if (
            self.sub is not None
            or self.args
            or self.series
        ):
            return None

        name = self.name.value
        return Command(
            name=name,
            args=[],
            series=[name],
            formula=column,
            lookback=lookback_zero
        )

    def create(
        self,
        context: Context
    ) -> Command:
        main_name = self.name.value
        commands = context.commands
        command_def = commands.get(main_name)

        if command_def is None:
            pure_command = self._empty_command(context)
            if pure_command is not None:
                return pure_command

            raise DirectiveValueError(
                context.input,
                f'unknown command "{main_name}"',
                self.name.loc
            )

        preset, sub_name = command_def.get_preset(self.name, self.sub, context)
        name = command_full_name(main_name, sub_name)

        args = self._coerce_args(name, preset, context)
        series = self._coerce_series(name, preset, context)

        return Command(
            name=name,
            args=args,
            series=series,
            formula=preset.formula,
            lookback=preset.lookback,
            preset=preset
        )

    def _coerce_args(
        self,
        name: str,
        preset: CommandPreset,
        context: Context
    ) -> List[PrimativeType]:
        preset_args = preset.args
        args = self.args

        max_length = len(preset_args)
        args_length = len(args)

        if args_length > max_length:
            raise DirectiveValueError(
                context.input,
                f'command "{name}" accepts max {max_length} args',
                self.loc
            )

        coerced = []

        for index, arg_def in enumerate(preset_args):
            default = arg_def.default
            setter = arg_def.coerce

            if index < args_length:
                arg_node = args[index]
                loc = arg_node.loc
                value = arg_node.create(context)
            else:
                # If the arg does not exist, use the command loc
                loc = self.loc
                value = None

            if value is None:
                value = default

            # Setter could be optional
            elif setter is not None:
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
                    f'args[{index}] is required for command "{name}"',
                    loc
                )

            coerced.append(value)

        return coerced

    def _coerce_series(
        self,
        name: str,
        preset: CommandPreset,
        context: Context
    ) -> List[CommandSeriesType]:
        preset_series = preset.series
        series = self.series

        max_length = len(preset_series)
        series_length = len(series)

        if series_length > max_length:
            raise DirectiveValueError(
                context.input,
                f'command "{name}" accepts max {max_length} series',
                self.loc
            )

        coerced = []

        for index, default in enumerate(preset_series):
            if index < series_length:
                value = series[index].create(context)
                if value is None:
                    value = default
            else:
                value = default

            if value is None:
                raise DirectiveValueError(
                    context.input,
                    f'series[{index}] is required for command "{name}"',
                    self.loc
                )

            coerced.append(value)

        return coerced


@dataclass(frozen=True, slots=True)
class ArgumentNode:
    loc: Loc
    # command:,2
    # -> [None, 2]
    value: Optional[ScalarNode[CommandArgInputType]]

    def create(self, context: Context):
        if self.value is None:
            return None

        return self.value.create(context)


@dataclass(frozen=True, slots=True)
class SeriesArgumentNode:
    loc: Loc
    value: Optional[SeriesNodeTypes]

    def create(self, context: Context):
        if self.value is None:
            return None

        return self.value.create(context)


@dataclass(frozen=True, slots=True)
class OperatorNode(Generic[OF]):
    loc: Loc
    name: str
    formula: OF
    priority: int

    def create(self, _: Context) -> Operator:
        return Operator[OF](
            name=self.name,
            formula=self.formula,
            priority=self.priority
        )


SeriesNodeTypes = Union[
    ExpressionNode,
    UnaryExpressionNode,
    CommandNode,
    str
]

ExpressionNodeTypes = Union[
    ScalarNode[NumberType],
    ExpressionNode,
    UnaryExpressionNode,
    CommandNode
]
