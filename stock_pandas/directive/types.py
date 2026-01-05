from __future__ import annotations
from typing import (
    Optional,
    Union,
    List,
    TYPE_CHECKING,
    Protocol,
    Generic,
    Callable
)
from dataclasses import dataclass, field

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


def _get_cumulative_lookback(expression: OperandType) -> int:
    if not isinstance(expression, Lookback):
        return 0

    return expression.cumulative_lookback


@dataclass
class Lookback:
    cumulative_lookback: int = field(init=False)

    def __post_init__(self):
        self.cumulative_lookback = self._cumulative_lookback()


@dataclass(slots=True)
class Expression(Lookback):
    operator: Operator[OperatorFormula]
    left: OperandType
    right: OperandType

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

    def _cumulative_lookback(self) -> int:
        right_lb = _get_cumulative_lookback(self.right)

        if self.left is None:
            return right_lb

        left_lb = _get_cumulative_lookback(self.left)
        return max(left_lb, right_lb)

    def run(
        self,
        df: StockDataFrame,
        s: slice
    ) -> ReturnType:
        return self.operator.formula(
            _run_expression(self.left, df, s),
            _run_expression(self.right, df, s)
        )


@dataclass(slots=True)
class UnaryExpression(Lookback):
    operator: Operator[UnaryOperatorFormula]
    expression: Directive

    def __str__(self) -> str:
        return f'{self.operator}{self.expression}'

    def _cumulative_lookback(self) -> int:
        return self.expression.cumulative_lookback

    def run(self, df: StockDataFrame, s: slice) -> ReturnType:
        return self.operator.formula(self.expression.run(df, s))


@dataclass(slots=True)
class Command(Lookback):
    """
    Args:
        lookback (CommandLookback): How many `np.nan`
    """

    name: str
    args: List[PrimativeType]
    series: List[CommandSeriesType]
    formula: CommandFormula
    lookback: CommandLookback
    preset: CommandPreset

    def __str__(self) -> str:
        stringify = (
            f'{self.name}:{join_args(self.args)}'
            if self.args
            else self.name
        )
        return f'({stringify})'

    def _cumulative_lookback(self) -> int:
        base_lb = self.lookback(*self.args)

        series_lb = max(
            _get_cumulative_lookback(series)
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
    priority: int

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


def DEFAULT_ARG_COERCE(x: PrimativeType) -> PrimativeType:
    return x

@dataclass(frozen=True, slots=True)
class CommandArg:
    """
    The definition of a command argument

    Args:
        default (Optional[PrimativeType] = None): The default value for the argument. `None` indicates that it is NOT an optional argument
        coerce (Optional[Callable[..., PrimativeType]]): The function to coerce the argument to the correct type and value range. The function is throwable.
    """

    default: Optional[PrimativeType] = None
    coerce: Callable[[CommandArgInputType], PrimativeType] = DEFAULT_ARG_COERCE


@dataclass(frozen=True, slots=True)
class CommandPreset:
    """
    A command preset defines the formula and arguments for a command

    Args:
        formula (CommandFormula): The formula of the command
        args (List[CommandArg]): The arguments of the command
    """

    formula: CommandFormula
    lookback: CommandLookback
    args: List[CommandArg] = field(default_factory=list)
    series: List[str] = field(default_factory=list)


Directive = Union[Expression, UnaryExpression, Command]
CommandSeriesType = Union[Directive, str]
