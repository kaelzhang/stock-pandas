from __future__ import annotations
from typing import (
    # Optional,
    Union,
    List,
    TYPE_CHECKING,
    Protocol,
    Generic
)
from dataclasses import dataclass

from stock_pandas.common import (
    join_args,
)

from .operator import (
    OperatorArgType,
    OperatorFormula,
    UnaryOperatorFormula,
    ReturnType,
    NumberType,
    OF
)

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame # pragma: no cover


def _run_expression(
    expression: OperandType,
    df: StockDataFrame,
    s: slice
) -> OperatorArgType:
    if isinstance(expression, (float, int)):
        return expression

    return expression.run(df, s)


@dataclass(frozen=True, slots=True)
class Expression:
    operator: OperatorFormula
    left: OperandType
    right: OperandType
    # root: bool = False

    # Use __str__ instead of __repr__,
    # for better debugging experience
    # - __str__ for user method invocation
    # - __repr__ for internal debugging
    def __str__(self) -> str:
        stringified = (
            f'{self.operator}{self.right}'
            if self.right is None
            else f'{self.operator}{self.operator}{self.right}'
        )

        return f'({stringified})'

        # return (
        #
        #     if self.root
        #     # We do not need to wrap the stringified directive
        #     # for top-level directives
        #     else stringified
        # )

    @property
    def cumulative_lookback(self) -> int:
        right_lb = self.right.cumulative_lookback()

        if self.left is None:
            return right_lb

        left_lb = self.left.cumulative_lookback()
        return max(left_lb, right_lb)

    def run(
        self,
        df: StockDataFrame,
        s: slice
    ) -> ReturnType:
        if self.left is None:
            return self.operator(_run_expression(self.right, df, s))

        return self.operator(
            _run_expression(self.left, df, s),
            _run_expression(self.right, df, s)
        )


@dataclass(frozen=True, slots=True)
class UnaryExpression:
    operator: UnaryOperatorFormula
    expression: Directive

    def __str__(self) -> str:
        return f'{self.operator}{self.expression}'

    @property
    def cumulative_lookback(self) -> int:
        return self.expression.cumulative_lookback()

    def run(self, df: StockDataFrame, s: slice) -> ReturnType:
        return self.operator(self.expression.run(df, s))


@dataclass(frozen=True, slots=True)
class Command:
    """
    Args:
        lookback (CommandLookback): How many `np.nan`
    """

    name: str
    args: List[PrimativeType]
    series: List[CommandSeriesType]
    formula: CommandFormula
    lookback: CommandLookback

    def __str__(self) -> str:
        return (
            f'{self.name}:{join_args(self.args)}'
            if self.args
            else self.name
        )

    @property
    def cumulative_lookback(self) -> int:
        base_lb = self.lookback(*self.args)

        series_lb = max(
            series.cumulative_lookback
            for series in self.series
        )

        # Since the current command calcuates based on the series,
        # the lookback increases
        return base_lb + series_lb

    def run(
        self,
        df: StockDataFrame,
        s: slice
    ) -> ReturnType:
        arrays = [
            (
                df.get_column(series)[s].to_numpy()
                if isinstance(series, str)
                else series.run(df, s)
            )
            for series in self.series
        ]

        return self.formula(*self.args, *arrays)


@dataclass(frozen=True, slots=True)
class Operator(Generic[OF]):
    name: str
    formula: OF

    def __str__(self) -> str:
        return self.name


OperandType = Union[Command, Expression, UnaryExpression, NumberType]
CommandArgInputType = Union[NumberType, str]
PrimativeType = Union[CommandArgInputType, bool]


class CommandFormula(Protocol):
    def __call__(
        self,
        # df: 'StockDataFrame',
        # s: slice,
        *args: Union[PrimativeType, ReturnType]
    ) -> ReturnType: ...


class CommandLookback(Protocol):
    def __call__(
        self,
        *args: PrimativeType
    ) -> int: ...


Directive = Union[Expression, UnaryExpression, Command]
CommandSeriesType = Union[Directive, str]
