#
# Tools
# ----------------------------------------------------

from functools import partial

import numpy as np

from stock_pandas.common import (
    repeat_to_int,
    period_to_int,
    style_enums,
    to_direction,
    rolling_calc,
    NDArrayAny
)

from stock_pandas.directive.command import (
    CommandDefinition,
    CommandPreset,
    CommandArg,
    lookback_zero
)
from stock_pandas.directive.types import ReturnType
from .base import BUILTIN_COMMANDS

from .common import (
    lookback_period
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
    repeat: int,
    direction: int,
    series: ReturnType
) -> ReturnType:
    period = repeat + 1

    current = NEGATIVE_INFINITY if direction == 1 else POSITIVE_INFINITY
    compare = partial(check_increase, direction, current)

    return rolling_calc(
        series,
        period,
        compare,
        False
    )

arg_repeat = CommandArg(1, repeat_to_int)

BUILTIN_COMMANDS['increase'] = CommandDefinition(
    CommandPreset(
        formula=increase,
        lookback=lookback_period,
        args=[
            arg_repeat,
            CommandArg(1, to_direction)
        ],
        series=[None]
    )
)

styles = dict(
    bullish=lambda c, o: c > o,
    bearish=lambda c, o: c < o
)


def style(
    style: str,
    open_series: ReturnType,
    close_series: ReturnType
) -> ReturnType:
    return styles[style](close_series, open_series)


BUILTIN_COMMANDS['style'] = CommandDefinition(
    CommandPreset(
        formula=style,
        lookback=lookback_zero,
        args=[
            CommandArg(coerce=style_enums)
        ],
        series=['open', 'close']
    )
)


def repeat(
    repeat: int,
    series: ReturnType
) -> ReturnType:
    if repeat == 1:
        return series

    return rolling_calc(
        series,
        repeat,
        np.all,
        False,
        1
    )


BUILTIN_COMMANDS['repeat'] = CommandDefinition(
    CommandPreset(
        formula=repeat,
        lookback=lookback_period,
        args=[arg_repeat],
        series=[None]
    )
)


def change(
    period: int,
    series: ReturnType
) -> ReturnType:
    """Get the percentage change for `on`
    """

    shift = period - 1

    shifted = np.roll(series, shift)
    # We perform a shift, not a roll
    shifted[:shift] = np.nan

    return series / shifted - 1


BUILTIN_COMMANDS['change'] = CommandDefinition(
    CommandPreset(
        formula=change,
        lookback=lookback_period,
        args=[CommandArg(2, period_to_int)],
        series=[None]
    )
)
