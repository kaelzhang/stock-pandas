#
# Tools
# ----------------------------------------------------

from functools import partial

import numpy as np

from stock_pandas.backend import use_rust
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

# Lazy imports for Rust implementations
_rs_increase = None
_rs_style = None
_rs_repeat = None
_rs_change = None


def _init_rust():
    """Lazy load Rust implementations."""
    global _rs_increase, _rs_style, _rs_repeat, _rs_change
    if _rs_increase is None:
        try:
            from stock_pandas_rs import (
                calc_increase,
                calc_style,
                calc_repeat,
                calc_change
            )
            _rs_increase = calc_increase
            _rs_style = calc_style
            _rs_repeat = calc_repeat
            _rs_change = calc_change
        except ImportError:
            pass


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
    _init_rust()
    if use_rust() and _rs_increase is not None:
        return np.asarray(_rs_increase(series.astype(float), repeat, direction))

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
    _init_rust()
    if use_rust() and _rs_style is not None:
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
    if repeat_count == 1:
        return series

    _init_rust()
    if use_rust() and _rs_repeat is not None:
        # Convert to boolean for Rust function
        bool_series = series.astype(bool)
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
    """Get the percentage change for `on`
    """
    _init_rust()
    if use_rust() and _rs_change is not None:
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
