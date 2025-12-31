from __future__ import annotations
from typing import (
    Optional,
    Tuple,
    Union,
    Callable,
    List,
    TYPE_CHECKING,
    Protocol
)
from dataclasses import dataclass
from numpy import ndarray

from stock_pandas.common import (
    join_args,
)

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame # pragma: no cover


@dataclass(frozen=True, slots=True)
class Directive:
    command: Command
    operator: Optional[Operator] = None
    expression: Optional[Expression] = None

    # Use __str__ instead of __repr__,
    # for better debugging experience
    # - __str__ for user method invocation
    # - __repr__ for internal debugging
    def __str__(self) -> str:
        return (
            f'{self.command}{self.operator}{self.expression}'
            if (
                self.operator is not None
                and self.expression is not None
            )
            else str(self.command)
        )

    def run(
        self,
        df: StockDataFrame,
        s: slice
    ) -> ReturnType:
        left, period_left = self.command.run(df, s)

        if not self.operator:
            return left, period_left

        expr = self.expression

        right, period_right = (
            expr.run(df, s)
            if isinstance(expr, Command)
            else (expr, 0)
        )

        operated = self.operator.formula(left, right)

        # Since 0.12.0
        # `operated` will not be of type np.nan

        # # Plan.A: `np.nan` makes non-sense, so mark them all as False
        # # or Plan.B: mark as `np.nan` ?
        # # Plan.A has better compatibility,
        # #   and `operated` is often used as condition indexer,
        # #   so it must be of bool type
        # operated = operated & is_not_nan(left) & is_not_nan(right)

        return operated, max(period_left, period_right)


@dataclass(frozen=True, slots=True)
class Command:
    name: str
    args: List[Argument]
    formula: CommandFormula

    def __str__(self) -> str:
        return (
            f'{self.name}:{join_args(self.args)}'
            if self.args
            else self.name
        )

    def run(
        self,
        df: StockDataFrame,
        s: slice
    ) -> ReturnType:
        args = [
            arg.arg_value
            for arg in self.args
        ]
        return self.formula(df, s, *args)


@dataclass(frozen=True, slots=True)
class Argument:
    """
    Args:
        value: The value of the argument.
        is_directive: Whether the argument is a directive.
    """

    value: ArgumentValue
    is_directive: bool = False

    @property
    def arg_value(self) -> CommandArgType:
        return (
            str(self.value)
            if self.is_directive
            else self.value
        )

    def __str__(self) -> str:
        return f'({self.value})' if self.is_directive else str(self.value)


@dataclass(frozen=True, slots=True)
class Operator:
    name: str
    formula: OperatorFormula

    def __str__(self) -> str:
        return self.name


CommandArgType = Union[str, int, float]
ReturnType = Tuple[
    ndarray,
    # The minimum periods to calculate the indicator,
    # which is actually `lookback + 1`
    int
]


class CommandFormula(Protocol):
    def __call__(
        self,
        df: 'StockDataFrame',
        s: slice,
        *args: CommandArgType
    ) -> ReturnType: ...


OperatorFormula = Callable[[ndarray, ndarray], ndarray]

Expression = Union[Command, float]
ArgumentValue = Union[CommandArgType, Directive]
