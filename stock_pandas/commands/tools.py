#
# Tools
# ----------------------------------------------------

from functools import partial

import numpy as np

from .base import (
    COMMANDS,
    CommandPreset,
    ReturnType
)

from stock_pandas.common import (
    repeat_to_int,
    period_to_int,
    style_enums,
    to_direction,

    rolling_calc
)


def column(df, s, column) -> ReturnType:
    """Gets the series of the column named `column`
    """

    return df.loc[s, column].to_numpy(), 0


COMMANDS['column'] = (
    CommandPreset(
        column,
        [(None, None)]
    ),
    None,
    None
)


POSITIVE_INFINITY = float('inf')
NEGATIVE_INFINITY = float('-inf')


def check_increase(direction, current, ndarray) -> bool:
    for value in ndarray:
        if (value - current) * direction > 0:
            current = value
        else:
            return False

    return True


def increase(df, s, on: str, repeat: int, direction: int) -> ReturnType:
    period = repeat + 1

    current = NEGATIVE_INFINITY if direction == 1 else POSITIVE_INFINITY
    compare = partial(check_increase, direction, current)

    return rolling_calc(
        df.exec(on)[s],
        period,
        compare,
        False
    ), period


COMMANDS['increase'] = (
    CommandPreset(
        increase,
        [
            (None, None),
            (1, repeat_to_int),
            (1, to_direction)
        ]
    ),
    None,
    None
)

styles = dict(
    bullish=lambda series: series['close'] > series['open'],
    bearish=lambda series: series['close'] < series['open']
)


def style(df, s, style: str) -> ReturnType:
    return df[s].apply(styles[style], axis=1).to_numpy(), 1


COMMANDS['style'] = (
    CommandPreset(
        style,
        [(None, style_enums)]
    ),
    None,
    None
)


def repeat(df, s, on: str, repeat: int) -> ReturnType:
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


COMMANDS['repeat'] = (
    CommandPreset(
        repeat,
        [
            (None, None),
            (1, repeat_to_int)
        ]
    ),
    None,
    None
)


def change(df, s, on: str, period: int) -> ReturnType:
    """Get the percentage change for `on`
    """

    target = df.exec(on)[s]

    shift = period - 1

    shifted = np.roll(target, shift)
    # We perform a shift, not a roll
    shifted[:shift] = np.nan

    return target / shifted - 1, period


COMMANDS['change'] = (
    CommandPreset(
        change,
        [
            (None, None),
            (2, period_to_int)
        ]
    ),
    None,
    None
)
