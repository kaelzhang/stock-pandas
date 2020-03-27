from typing import (
    Optional,
    Tuple,
    Callable
)

from numpy import ndarray

from stock_pandas.common import (
    join_args,
    command_full_name
)


class Directive:
    __slots__ = (
        'command',
        'operator',
        'expression'
    )

    def __init__(
        self,
        command: 'Command',
        operator: Optional['Operator'] = None,
        expression: Optional['Command'] = None
    ) -> None:
        self.command = command
        self.operator = operator
        self.expression = expression

    def __str__(self) -> str:
        return f'{self.command}{self.operator}{self.expression}' \
            if self.operator else str(self.command)

    def run(self, df, s: slice) -> Tuple[ndarray, int]:
        left, period_left = self.command.run(df, s)

        if not self.operator:
            return left, period_left

        expr = self.expression

        right, period_right = expr.run(df, s) if isinstance(expr, Command) \
            else (expr, 0)

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


class Command:
    __slots__ = (
        'name',
        'sub',
        'args',
        'formula'
    )

    def __init__(
        self,
        name: str,
        sub: Optional[str],
        args: list,
        formula: Callable[..., Tuple[ndarray, int]]
    ) -> None:
        self.name = name
        self.sub = sub
        self.args = args
        self.formula = formula

    def __str__(self) -> str:
        name = command_full_name(self.name, self.sub)

        return f'{name}:{join_args(self.args)}' \
            if self.args else name

    def run(self, df, s: slice):
        args = [arg.value for arg in self.args]
        return self.formula(df, s, *args)


class Argument:
    __slots__ = (
        'value',
        'is_directive'
    )

    def __init__(self, value: str, is_directive: bool = False) -> None:
        self.value = value
        self.is_directive = is_directive

    def __str__(self) -> str:
        return f'({self.value})' if self.is_directive else str(self.value)


class Operator:
    __slots__ = (
        'name',
        'formula'
    )

    def __init__(
        self,
        name: str,
        formula: Callable[[ndarray, ndarray], ndarray]
    ) -> None:
        self.name = name
        self.formula = formula

    def __str__(self) -> str:
        return self.name
