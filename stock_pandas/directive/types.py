from __future__ import annotations
from typing import (
    Optional,
    Union,
    List,
    TYPE_CHECKING,
    Protocol,
    Generic,
    Callable,
    Literal
)
from dataclasses import dataclass, field

from stock_pandas.common import (
    join_args,
    EMPTY
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
    _str: Optional[str] = field(init=False, repr=False)

    def __str__(self) -> str:
        return self._str

    def __post_init__(self):
        self.cumulative_lookback = self._cumulative_lookback()
        self._str = self._stringify()


@dataclass(slots=True)
class Expression(Lookback):
    operator: Operator[OperatorFormula]
    left: OperandType
    right: OperandType

    # Use __str__ instead of __repr__,
    # for better debugging experience
    # - __str__ for user method invocation
    # - __repr__ for internal debugging
    def _stringify(self) -> str:
        left_str = (
            f'({str(self.left)})'
            if (
                isinstance(self.left, Expression)
                and self.left.operator.priority < self.operator.priority

            )
            else str(self.left)
        )

        right_str = (
            f'({str(self.right)})'
            if (
                isinstance(self.right, Expression)
                # If the right operator has the same priority,
                # we still need to wrap the right expression in parentheses,
                # because two operators with the same priority
                # are left-associative
                and self.right.operator.priority <= self.operator.priority

            )
            else str(self.right)
        )

        return f'{left_str}{self.operator}{right_str}'

    def _cumulative_lookback(self) -> int:
        return max(
            _get_cumulative_lookback(self.right),
            _get_cumulative_lookback(self.left)
        )

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

    def _stringify(self) -> str:
        if isinstance(self.expression, Command):
            return f'{self.operator}{self.expression}'

        return f'{self.operator}({self.expression})'

    def _cumulative_lookback(self) -> int:
        return self.expression.cumulative_lookback

    def run(self, df: StockDataFrame, s: slice) -> ReturnType:
        return self.operator.formula(self.expression.run(df, s))



_StringifyKey = Literal['args', 'series']
_StringifyPrefix = Literal[':', '@']

COMMAND_COLUMN_NAME = '__close__'


@dataclass(slots=True)
class Command(Lookback):
    """
    Args:
        lookback (CommandLookback): How many `np.nan`
    """

    name: str
    args: List[PrimativeType]
    series: List[CommandSeriesType]
    preset: CommandPreset

    def _stringify(self) -> str:
        if self.name == COMMAND_COLUMN_NAME:
            return self.series[0]

        return (
            self.name
            + self._stringify_args('args', ':')
            + self._stringify_args('series', '@')
        )

    def _stringify_args(
        self,
        key: _StringifyKey,
        prefix: _StringifyPrefix
    ) -> str:
        args = getattr(self, key)

        if not args:
            return EMPTY

        to_join = []
        for i, arg_def in enumerate(getattr(self.preset, key)):
            arg = args[i]
            to_join.append(
                EMPTY if arg == arg_def.default else arg
            )

        while to_join and to_join[-1] == EMPTY:
            to_join.pop()

        if not to_join:
            return EMPTY

        return prefix + join_args(to_join)

    def _cumulative_lookback(self) -> int:
        base_lb = self.preset.lookback(*self.args)

        series_lbs = [
            _get_cumulative_lookback(series)
            for series in self.series
        ]

        # There might be no series lookback
        series_lb = max(series_lbs) if series_lbs else 0

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

        return self.preset.formula(*self.args, *arrays)


@dataclass(frozen=True, slots=True)
class Operator(Generic[OF]):
    name: str
    formula: OF = field(repr=False)
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
    coerce: Callable[[CommandArgInputType], PrimativeType] = field(
        default=DEFAULT_ARG_COERCE,
        repr=False
    )


@dataclass(frozen=True, slots=True)
class CommandPreset:
    """
    A command preset defines the formula and arguments for a command

    Args:
        formula (CommandFormula): The formula of the command
        args (List[CommandArg]): The arguments of the command
    """

    formula: CommandFormula = field(repr=False)
    lookback: CommandLookback = field(repr=False)
    args: List[CommandArg] = field(default_factory=list)
    series: List[CommandArg] = field(default_factory=list)


Directive = Union[Expression, UnaryExpression, Command]
CommandSeriesType = Union[Directive, str]
