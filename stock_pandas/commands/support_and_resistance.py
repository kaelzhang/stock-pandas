#
# Dynamic support and resistance indicators
# ----------------------------------------------------

from functools import partial

import numpy as np

from stock_pandas.common import (
    period_to_int,
    times_to_float,
    rolling_calc
)

from stock_pandas.directive.command import CommandDefinition
from stock_pandas.directive.types import (
    ReturnType,
    CommandPreset,
    CommandArg
)
from stock_pandas.meta.time_frame import (
    timeFrames,
    TimeFrame
)

from .base import BUILTIN_COMMANDS
from .common import (
    lookback_period,
    series_close
)
from .trend_following import ma


# boll
# ----------------------------------------------------

def boll(
    period: int,
    series: ReturnType
) -> ReturnType:
    """Gets the mid band of bollinger bands
    """
    return ma(period, series)


def boll_band(
    upper: bool,
    period: int,
    times: float,
    series: ReturnType
) -> ReturnType:
    """Gets the upper band or the lower band of bolinger bands

    Args:
        upper (bool): Get the upper band if True else the lower band
    """

    # prices = df.get_column(column)[s].to_numpy()

    # ma = df.exec(f'ma:{period},{column}')[s]
    ma_series = ma(period, series)

    # Unlike historical volatility (HV),
    # for bollinger bands, we use the population standard deviation (n)
    # ref: https://en.wikipedia.org/wiki/Bollinger_Bands
    mstd = rolling_calc(series, period, np.std)

    if upper:
        return np.add(ma_series, np.multiply(times, mstd))
    else:
        return np.subtract(ma_series, np.multiply(times, mstd))


arg_boll_period = CommandArg(20, period_to_int)
args_boll = [
    arg_boll_period
]
args_boll_band = [
    arg_boll_period,
    CommandArg(2., times_to_float)
]

BUILTIN_COMMANDS['boll'] = CommandDefinition(
    CommandPreset(
        formula=boll,
        lookback=lookback_period,
        args=args_boll,
        series=series_close
    ),
    {
        'upper': CommandPreset(
            formula=partial[ReturnType](boll_band, True),
            lookback=lookback_period,
            args=args_boll_band,
            series=series_close
        ),
        'lower': CommandPreset(
            formula=partial[ReturnType](boll_band, False),
            lookback=lookback_period,
            args=args_boll_band,
            series=series_close
        )
    },
    {
        'u': 'upper',
        'l': 'lower'
    }
)


def bbw(
    period: int,
    series: ReturnType
) -> ReturnType:
    """Gets the width of bollinger bands
    """

    ma_series = ma(period, series)
    mstd = rolling_calc(series, period, np.std)

    return np.divide(
        np.multiply(4, mstd),
        ma_series
    )


BUILTIN_COMMANDS['bbw'] = CommandDefinition(
    CommandPreset(
        formula=bbw,
        lookback=lookback_period,
        args=args_boll,
        series=series_close
    )
)


DAY_MINUTES = TimeFrame.D1.minutes

def hv(
    period: int,
    minutes: int,
    trading_days: int,
    close: ReturnType
) -> ReturnType:
    """Gets the historical volatility of the stock
    """

    shifted = np.roll(close, 1)
    shifted[0] = np.nan
    log_return = np.log(close / shifted)

    rolling_std = rolling_calc(
        log_return,
        period,
        # We must use ddof=1 to get the sample standard deviation (n-1)
        # for historical volatility.
        partial(np.std, ddof=1)
    )

    return rolling_std * np.sqrt(trading_days * DAY_MINUTES / minutes)


def lookback_hv(period: int, *_) -> int:
    return period


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
    CommandPreset(
        formula=hv,
        lookback=lookback_hv,
        args=[
            CommandArg(coerce=period_to_int),
            CommandArg(DAY_MINUTES, time_frame_to_minutes),
            CommandArg(252, trading_days_to_int)
        ],
        series=series_close
    )
)
