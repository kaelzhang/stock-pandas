#
# Tools
# ----------------------------------------------------

from functools import partial

import numpy as np

from .base import (
    COMMANDS,
    CommandPreset
)

from stock_pandas.common import (
    repeat_to_int,
    style_enums,
    to_direction,

    rolling_calc
)


def column(df, s, column):
    """Gets the series of the column named `column`
    """

    return df.loc[s, column].to_numpy(), 0


COMMANDS['column'] = CommandPreset(
    column,
    [(None, None)]
)


POSITIVE_INFINITY = float('inf')
NEGATIVE_INFINITY = float('-inf')


def check_increase(direction, current, ndarray):
    for value in ndarray:
        if (value - current) * direction > 0:
            current = value
        else:
            return False

    return True


def increase(df, s, on_what: str, repeat: int, direction: int):
    period = repeat + 1

    current = NEGATIVE_INFINITY if direction == 1 else POSITIVE_INFINITY
    compare = partial(check_increase, direction, current)

    return rolling_calc(
        df.exec(on_what)[s],
        period,
        compare,
        False
    ), period


COMMANDS['increase'] = CommandPreset(
    increase,
    [
        (None, None),
        (1, repeat_to_int),
        (1, to_direction)
    ]
)

styles = dict(
    bullish=lambda series: series['close'] > series['open'],
    bearish=lambda series: series['close'] < series['open']
)


def style(df, s, style: str):
    return df[s].apply(styles[style], axis=1).to_numpy(), 1


COMMANDS['style'] = CommandPreset(
    style,
    [(None, style_enums)]
)


def repeat(df, s, command_str: str, repeat: int):
    result = df.exec(command_str)[s]

    if repeat == 1:
        return result, repeat

    return rolling_calc(
        result,
        repeat,
        np.all,
        False,
        1
    ), repeat


COMMANDS['repeat'] = CommandPreset(
    repeat,
    [
        (None, None),
        (1, repeat_to_int)
    ]
)
