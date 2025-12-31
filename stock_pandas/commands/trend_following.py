#
# Trend-following momentum indicators
# ----------------------------------------------------

from typing import TYPE_CHECKING

from pandas import concat

from stock_pandas.common import (
    period_to_int,
)

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame  # pragma: no cover

from stock_pandas.math.ma import (
    calc_ma,
    calc_ewma
)

from stock_pandas.directive.command import (
    CommandDefinition,
    CommandPreset,
    CommandArg
)
from stock_pandas.directive.types import ReturnType
from .base import BUILTIN_COMMANDS

from .args import (
    arg_period
)


# ma
# ----------------------------------------------------


def ma(df: 'StockDataFrame', s: slice, period: int, on: str) -> ReturnType:
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

    return calc_ma(
        df.exec(on)[s],
        period
    ), period


args_ma = [
    # parameter setting for `period`
    arg_period,
    # setting for `column`
    CommandArg(
        # The default value of the second parameter
        'close',
        # If the command use the default value,
        # then it will skip validating
    )
]

BUILTIN_COMMANDS['ma'] = CommandDefinition(
    CommandPreset(ma, args_ma)
)


# ema
# ----------------------------------------------------

def ema(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    column: str
) -> ReturnType:
    """Gets Exponential Moving Average
    """

    return calc_ewma(
        df.get_column(column)[s].to_numpy(),
        period
    ), period


BUILTIN_COMMANDS['ema'] = CommandDefinition(
    CommandPreset(ema, args_ma)
)


# macd
# ----------------------------------------------------

def macd(
    df: 'StockDataFrame',
    s: slice,
    fast_period: int,
    slow_period: int
) -> ReturnType:
    fast = df.exec(f'ema:{fast_period},close', False)[s]
    slow = df.exec(f'ema:{slow_period},close', False)[s]

    return fast - slow, fast_period


def macd_signal(
    df: 'StockDataFrame',
    s: slice,
    fast_period: int,
    slow_period: int,
    signal_period: int
) -> ReturnType:
    macd = df.exec(f'macd:{fast_period},{slow_period}')[s]

    return calc_ewma(macd, signal_period), fast_period


MACD_HISTOGRAM_TIMES = 2.0


def macd_histogram(
    df: 'StockDataFrame',
    s: slice,
    fast_period: int,
    slow_period: int,
    signal_period: int
) -> ReturnType:
    macd = df.exec(f'macd:{fast_period},{slow_period}')[s]
    macd_s = df.exec(
        f'macd.signal:{fast_period},{slow_period},{signal_period}'
    )[s]

    return MACD_HISTOGRAM_TIMES * (macd - macd_s), fast_period


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
        macd,
        args_macd
    ),
    dict(
        signal=CommandPreset(macd_signal, args_macd_all),
        histogram=CommandPreset(macd_histogram, args_macd_all)
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
    df: 'StockDataFrame',
    _: slice,
    a: int,
    b: int,
    c: int,
    d: int
) -> ReturnType:
    """Calculates BBI (Bull and Bear Index) which is the average of
    ma:3, ma:6, ma:12, ma:24 by default
    """
    return (
        df.exec(f'ma:{a}')
        + df.exec(f'ma:{b}')
        + df.exec(f'ma:{c}')
        + df.exec(f'ma:{d}')
    ) / 4, max(a, b, c, d)


BUILTIN_COMMANDS['bbi'] = CommandDefinition(
    CommandPreset(
        bbi,
        [
            CommandArg(3, period_to_int),
            CommandArg(6, period_to_int),
            CommandArg(12, period_to_int),
            CommandArg(24, period_to_int)
        ]
    )
)


# atr
# Ref: https://www.investopedia.com/terms/a/atr.asp
# ----------------------------------------------------

def atr(df: 'StockDataFrame', s: slice, period: int) -> ReturnType:
    """Calculates TR (True Range)
    """

    prev_close = df.get_column('close')[s].shift(1)
    high = df.get_column('high')[s]
    low = df.get_column('low')[s]

    # True range
    tr = concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1).to_numpy()

    return calc_ma(tr, period), period + 1


BUILTIN_COMMANDS['atr'] = CommandDefinition(
    CommandPreset(atr, [
        CommandArg(14, period_to_int)
    ])
)
