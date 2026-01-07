#
# Tools
# ----------------------------------------------------

from functools import partial

import numpy as np

from stock_pandas.backend import use_rust, is_rust_available
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
    lookback_zero
)
from stock_pandas.directive.types import (
    ReturnType,
    CommandPreset,
    CommandArg
)
from .base import BUILTIN_COMMANDS

from .common import (
    lookback_period,
    create_series_args,
    series_required
)

# Import Rust implementations if available
if is_rust_available():
    from stock_pandas_rs import (
        calc_increase as _rs_increase,
        calc_style as _rs_style,
        calc_repeat as _rs_repeat,
        calc_change as _rs_change
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
    if use_rust():
        return np.asarray(
            _rs_increase(series.astype(float), repeat, direction)
        )

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
        series=series_required
    )
)

styles = dict(
    bullish=lambda c, o: c > o,
    bearish=lambda c, o: c < o
)


def style(
    style_name: str,
    open_series: ReturnType,
    close_series: ReturnType
) -> ReturnType:
    if use_rust():
        return np.asarray(_rs_style(
            style_name,
            open_series.astype(float),
            close_series.astype(float)
        ))

    return styles[style_name](close_series, open_series)


BUILTIN_COMMANDS['style'] = CommandDefinition(
    CommandPreset(
        formula=style,
        lookback=lookback_zero,
        args=[
            CommandArg(coerce=style_enums)
        ],
        series=create_series_args(['open', 'close'])
    )
)


def repeat(
    repeat_count: int,
    series: ReturnType
) -> ReturnType:
    """
    Check if the series will repeat `repeat_count` times.
    """

    if repeat_count == 1:
        return series

    # Convert to boolean for Rust function
    bool_series = series.astype(bool)

    if use_rust():
        return np.asarray(_rs_repeat(bool_series, repeat_count))

    return rolling_calc(
        series,
        repeat_count,
        np.all,
        False,
        1
    )


BUILTIN_COMMANDS['repeat'] = CommandDefinition(
    CommandPreset(
        formula=repeat,
        lookback=lookback_period,
        args=[arg_repeat],
        series=series_required
    )
)


def change(
    period: int,
    series: ReturnType
) -> ReturnType:
    """Get the percentage change for `series`
    """
    if use_rust():
        return np.asarray(_rs_change(series.astype(float), period))

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
        series=series_required
    )
)
