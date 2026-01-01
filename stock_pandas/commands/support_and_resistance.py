#
# Dynamic support and resistance indicators
# ----------------------------------------------------

from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from stock_pandas.common import (
    period_to_int,
    times_to_float,
    rolling_calc
)

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame  # pragma: no cover

from stock_pandas.directive.command import (
    CommandDefinition,
    CommandPreset,
    CommandArg,
)
from stock_pandas.directive.types import ReturnType
from stock_pandas.meta.time_frame import (
    timeFrames,
    TimeFrame
)

from .base import BUILTIN_COMMANDS

from .args import (
    arg_column_close
)

# boll
# ----------------------------------------------------

def boll(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    column: str
) -> ReturnType:
    """Gets the mid band of bollinger bands
    """
    return df.exec(f'ma:{period},{column}')[s], period


def boll_band(
    upper: bool,
    df: 'StockDataFrame',
    s: slice,
    period: int,
    times: float,
    column: str
) -> ReturnType:
    """Gets the upper band or the lower band of bolinger bands

    Args:
        upper (bool): Get the upper band if True else the lower band
    """

    prices = df.get_column(column)[s].to_numpy()

    ma = df.exec(f'ma:{period},{column}')[s]

    # Unlike historical volatility (HV),
    # for bollinger bands, we use the population standard deviation (n)
    # ref: https://en.wikipedia.org/wiki/Bollinger_Bands
    mstd = rolling_calc(
        prices,
        period,
        np.std
    )

    if upper:
        return np.add(ma, np.multiply(times, mstd)), period
    else:
        return np.subtract(ma, np.multiply(times, mstd)), period


arg_boll_period = CommandArg(20, period_to_int)
args_boll = [
    arg_boll_period,
    arg_column_close
]
args_boll_band = [
    arg_boll_period,
    CommandArg(2., times_to_float),
    arg_column_close
]

BUILTIN_COMMANDS['boll'] = CommandDefinition(
    CommandPreset(boll, args_boll),
    dict(
        upper=CommandPreset(
            partial(boll_band, True),
            args_boll_band
        ),
        lower=CommandPreset(
            partial(boll_band, False),
            args_boll_band
        ),
    ),
    dict(
        u='upper',  # noqa
        l='lower'   # noqa
    )
)


def bbw(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    column: str
) -> ReturnType:
    """Gets the width of bollinger bands
    """

    prices = df.get_column(column)[s].to_numpy()
    ma = df.exec(f'ma:{period},{column}')[s]
    mstd = rolling_calc(
        prices,
        period,
        np.std
    )

    return np.divide(
        np.multiply(4, mstd),
        ma
    ), period


BUILTIN_COMMANDS['bbw'] = CommandDefinition(
    CommandPreset(bbw, args_boll)
)


DAY_MINUTES = TimeFrame.D1.minutes

def hv(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    minutes: int,
    trading_days: int
) -> ReturnType:
    """Gets the historical volatility of the stock
    """

    close = df.get_column('close')[s]
    log_return = np.log(close / close.shift(1))
    rolling_std = log_return.rolling(
        window=period,
        min_periods=period

    # We must use ddof=1 to get the sample standard deviation (n-1)
    # for historical volatility.
    ).std(ddof=1)

    return (
        rolling_std * np.sqrt(trading_days * DAY_MINUTES / minutes),
        period + 1
    )


def trading_days_to_int(value: str) -> int:
    try:
        days = int(value)
    except ValueError:
        raise ValueError(f'`{value}` is not a valid trading days')

    if days <= 0 or days > 365:
        raise ValueError(
            f'trading days must be greater than 0 and less than 365, but got `{days}`'
        )

    return days


def time_frame_to_minutes(value: str) -> int:
    time_frame = timeFrames.get(value)

    if time_frame is None:
        raise ValueError(f'`{value}` is not a valid time frame')

    return time_frame.minutes


BUILTIN_COMMANDS['hv'] = CommandDefinition(
    CommandPreset(hv, [
        CommandArg(coerce=period_to_int),
        CommandArg(DAY_MINUTES, time_frame_to_minutes),
        CommandArg(252, trading_days_to_int)
    ])
)
