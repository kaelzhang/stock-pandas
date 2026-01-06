#
# Trend-following momentum indicators
# ----------------------------------------------------

import numpy as np

from stock_pandas.backend import use_rust, is_rust_available
from stock_pandas.common import (
    period_to_int,
)

from stock_pandas.math.ma import (
    calc_ma,
    calc_ewma
)

from stock_pandas.directive.command import CommandDefinition
from stock_pandas.directive.types import (
    ReturnType,
    CommandPreset,
    CommandArg
)
from .base import BUILTIN_COMMANDS

from .common import (
    arg_period,
    lookback_period,
    series_close,
    create_series_args
)

# Import Rust implementations if available
if is_rust_available():
    from stock_pandas_rs import (
        calc_macd as _rs_macd,
        calc_macd_signal as _rs_macd_signal,
        calc_macd_histogram as _rs_macd_histogram,
        calc_bbi as _rs_bbi,
        calc_atr as _rs_atr
    )


# ma
# ----------------------------------------------------


def ma(period: int, on: ReturnType) -> ReturnType:
    """Gets simple moving average

    Args:
        df (StockDataFrame): the stock data frame itself
        s (slice): the slice object
        period (int): size of the moving period
        on (str): the target that is based on to calculate

    Returns:
        Tuple[np.ndarray, int]: the numpy ndarray object,
        and the period offset the indicator needs
    """

    return calc_ma(on, period)


args_ma = [arg_period]

BUILTIN_COMMANDS['ma'] = CommandDefinition(
    CommandPreset(
        formula=ma,
        lookback=lookback_period,
        args=args_ma,
        series=series_close
    )
)


# ema
# ----------------------------------------------------

def ema(period: int, series: ReturnType) -> ReturnType:
    """Gets Exponential Moving Average
    """

    return calc_ewma(series, period)


BUILTIN_COMMANDS['ema'] = CommandDefinition(
    CommandPreset(
        formula=ema,
        lookback=lookback_period,
        args=args_ma,
        series=series_close
    )
)


# macd
# ----------------------------------------------------

def macd(
    fast_period: int,
    slow_period: int,
    series: ReturnType
) -> ReturnType:
    if use_rust():
        return np.asarray(_rs_macd(series.astype(float), fast_period, slow_period))

    fast = ema(fast_period, series)
    slow = ema(slow_period, series)

    return fast - slow

def lookback_macd(fast_period: int, slow_period: int) -> int:
    return max(fast_period, slow_period) - 1


def macd_signal(
    fast_period: int,
    slow_period: int,
    signal_period: int,
    series: ReturnType
) -> ReturnType:
    if use_rust():
        return np.asarray(_rs_macd_signal(
            series.astype(float), fast_period, slow_period, signal_period
        ))

    macd_series = macd(fast_period, slow_period, series)

    return calc_ewma(macd_series, signal_period)

def lookback_macd_signal(
    fast_period: int, slow_period: int, signal_period: int
) -> int:
    return max(fast_period, slow_period) + signal_period - 2


MACD_HISTOGRAM_TIMES = 2.0


def macd_histogram(
    fast_period: int,
    slow_period: int,
    signal_period: int,
    series: ReturnType
) -> ReturnType:
    if use_rust():
        return np.asarray(_rs_macd_histogram(
            series.astype(float), fast_period, slow_period, signal_period
        ))

    macd_series = macd(fast_period, slow_period, series)
    macd_signal_series = macd_signal(
        fast_period, slow_period, signal_period, series
    )

    return MACD_HISTOGRAM_TIMES * (macd_series - macd_signal_series)


args_macd =[
    # Fast period
    CommandArg(12, period_to_int),
    # Slow period
    CommandArg(26, period_to_int)
]

args_macd_all = [
    *args_macd,
    CommandArg(9, period_to_int)
]

BUILTIN_COMMANDS['macd'] = CommandDefinition(
    CommandPreset(
        formula=macd,
        lookback=lookback_macd,
        args=args_macd,
        series=series_close
    ),
    dict(
        signal=CommandPreset(
            formula=macd_signal,
            lookback=lookback_macd_signal,
            args=args_macd_all,
            series=series_close
        ),
        histogram=CommandPreset(
            formula=macd_histogram,
            lookback=lookback_macd_signal,
            args=args_macd_all,
            series=series_close
        )
    ),
    dict(
        s='signal',
        h='histogram',

        # In some countries, such as China,
        # the three series are commonly known as:
        dif=None,
        dea='signal',
        macd='histogram'
    )
)


# bbi
# ----------------------------------------------------

def bbi(
    a: int,
    b: int,
    c: int,
    d: int,
    close_series: ReturnType
) -> ReturnType:
    """Calculates BBI (Bull and Bear Index) which is the average of
    ma:3, ma:6, ma:12, ma:24 by default
    """
    if use_rust():
        return np.asarray(_rs_bbi(close_series.astype(float), a, b, c, d))

    return (
        ma(a, close_series)
        + ma(b, close_series)
        + ma(c, close_series)
        + ma(d, close_series)
    ) / 4

def lookback_bbi(a: int, b: int, c: int, d: int) -> int:
    return max(a, b, c, d)


BUILTIN_COMMANDS['bbi'] = CommandDefinition(
    CommandPreset(
        formula=bbi,
        lookback=lookback_bbi,
        args=[
            CommandArg(3, period_to_int),
            CommandArg(6, period_to_int),
            CommandArg(12, period_to_int),
            CommandArg(24, period_to_int)
        ],
        series=series_close
    )
)


# atr
# Ref: https://www.investopedia.com/terms/a/atr.asp
# ----------------------------------------------------

def atr(
    period: int,
    high: ReturnType,
    low: ReturnType,
    close: ReturnType
) -> ReturnType:
    """Calculates TR (True Range)
    """
    if use_rust():
        return np.asarray(_rs_atr(
            high.astype(float),
            low.astype(float),
            close.astype(float),
            period
        ))

    prev_close = np.roll(close, 1)
    prev_close[0] = np.nan

    # True range
    tr = np.maximum.reduce([
        np.absolute(high - low),
        np.absolute(high - prev_close),
        np.absolute(low - prev_close),
    ])

    return calc_ma(tr, period)


def lookback_atr(period: int) -> int:
    return period


BUILTIN_COMMANDS['atr'] = CommandDefinition(
    CommandPreset(
        formula=atr,
        lookback=lookback_atr,
        args=[
            CommandArg(14, period_to_int)
        ],
        series=create_series_args(['high', 'low', 'close'])
    )
)
