from __future__ import annotations
import operator
from typing import (
    Optional,
    Tuple,
    Union,
    Callable,
    List,
    Any,
    TYPE_CHECKING,
    Protocol
)
from dataclasses import dataclass
from numpy.typing import NDArray

from stock_pandas.common import (
    join_args,
)
from stock_pandas.directive.cache import DirectiveCache

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame # pragma: no cover


def _run_expression(
    expression: OperandType,
    df: StockDataFrame,
    s: slice
) -> OperatorArgType:
    if isinstance(expression, float):
        return expression

    return expression.run(df, s)


@dataclass(frozen=True, slots=True)
class Expression:
    operator: Union[OperatorFormula, UnaryOperatorFormula]
    left: Optional[OperandType] = None
    right: Optional[OperandType] = None
    root: bool = False

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

        return (
            f'({stringified})'
            if self.root
            # We do not need to wrap the stringified directive
            # for top-level directives
            else stringified
        )

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
            return self.operator.formula(_run_expression(self.right, df, s))

        return self.operator.formula(
            _run_expression(self.left, df, s),
            _run_expression(self.right, df, s)
        )


@dataclass(frozen=True, slots=True)
class Command:
    """
    Args:
        lookback (CommandLookback): How many `np.nan`
    """

    name: str
    params: List[PrimativeType]
    series: List[Command, Expression]
    formula: CommandFormula
    lockback: CommandLookback
    root: bool = False

    def __str__(self) -> str:
        return (
            f'{self.name}:{join_args(self.args)}'
            if self.args
            else self.name
        )

    @property
    def cumulative_lookback(self) -> int:
        base_lb = self.lockback(*self.params)

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
            series.run(df, s)
            for series in self.series
        ]

        return self.formula(*self.params, *arrays)


@dataclass(frozen=True, slots=True)
class Operator:
    name: str
    formula: OperatorFormula

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class UnaryOperator:
    name: str
    formula: UnaryOperatorFormula

    def __str__(self) -> str:
        return self.name


OperandType = Union[Command, Expression, float]
PrimativeType = Union[str, int, float]
ReturnType = NDArray[Any]


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


OperatorArgType = Union[float, ReturnType]
OperatorFormula = Callable[[OperatorArgType, OperatorArgType], ReturnType]
UnaryOperatorFormula = Callable[[OperatorArgType], ReturnType]

Directive = Union[Expression, Command]
