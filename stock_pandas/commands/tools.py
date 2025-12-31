#
# Tools
# ----------------------------------------------------

from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from stock_pandas.common import (
    repeat_to_int,
    period_to_int,
    style_enums,
    to_direction,
    rolling_calc,
    NDArrayAny
)

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame  # pragma: no cover

from stock_pandas.directive.command import (
    CommandDefinition,
    CommandPreset,
    CommandArg,
)
from stock_pandas.directive.types import ReturnType
from .base import BUILTIN_COMMANDS

from .args import (
    arg_required
)


def column(df: 'StockDataFrame', s: slice, column: str) -> ReturnType:
    """Gets the series of the column named `column`
    """

    return df.loc[s, column].to_numpy(), 0


# TODO:
# Posibility to deprecate this command
BUILTIN_COMMANDS['column'] = CommandDefinition(
    CommandPreset(column, [arg_required])
)


POSITIVE_INFINITY = float('inf')
NEGATIVE_INFINITY = float('-inf')


def check_increase(
    direction: int,
    current: float,
    ndarray: NDArrayAny
) -> bool:
    for value in ndarray:
        if (value - current) * direction > 0:
            current = value
        else:
            return False

    return True


def increase(
    df: 'StockDataFrame',
    s: slice,
    on: str,
    repeat: int,
    direction: int
) -> ReturnType:
    period = repeat + 1

    current = NEGATIVE_INFINITY if direction == 1 else POSITIVE_INFINITY
    compare = partial(check_increase, direction, current)

    return rolling_calc(
        df.exec(on)[s],
        period,
        compare,
        False
    ), period

arg_repeat = CommandArg(1, repeat_to_int)

BUILTIN_COMMANDS['increase'] = CommandDefinition(
    CommandPreset(
        increase,
        [
            arg_required,
            arg_repeat,
            CommandArg(1, to_direction)
        ]
    )
)

styles = dict(
    bullish=lambda series: series['close'] > series['open'],
    bearish=lambda series: series['close'] < series['open']
)


def style(df: 'StockDataFrame', s: slice, style: str) -> ReturnType:
    return df.iloc[s].apply(styles[style], axis=1).to_numpy(), 1


BUILTIN_COMMANDS['style'] = CommandDefinition(
    CommandPreset(
        style,
        [
            CommandArg(coerce=style_enums)
        ]
    )
)


def repeat(
    df: 'StockDataFrame',
    s: slice,
    on: str,
    repeat: int
) -> ReturnType:
    result = df.exec(on)[s]

    if repeat == 1:
        return result, repeat

    return rolling_calc(
        result,
        repeat,
        np.all,
        False,
        1
    ), repeat


BUILTIN_COMMANDS['repeat'] = CommandDefinition(
    CommandPreset(
        repeat,
        [
            arg_required,
            arg_repeat,
        ]
    )
)


def change(
    df: 'StockDataFrame',
    s: slice,
    on: str,
    period: int
) -> ReturnType:
    """Get the percentage change for `on`
    """

    target = df.exec(on)[s]

    shift = period - 1

    shifted = np.roll(target, shift)
    # We perform a shift, not a roll
    shifted[:shift] = np.nan

    return target / shifted - 1, period


BUILTIN_COMMANDS['change'] = CommandDefinition(
    CommandPreset(
        change,
        [
            arg_required,
            CommandArg(2, period_to_int)
        ]
    )
)
