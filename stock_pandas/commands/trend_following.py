#
# Trend-following momentum indicators
# ----------------------------------------------------

from .base import (
    COMMANDS,
    CommandPreset,
    ReturnType,

    arg_period
)

from stock_pandas.common import (
    period_to_int,
    column_enums
)

from stock_pandas.math.ma import (
    calc_ma,
    calc_ewma
)

# ma
# ----------------------------------------------------


def ma(df, s, period, column) -> ReturnType:
    """Gets simple moving average

    Args:
        df (StockDataFrame): the stock data frame itself
        s (slice): the slice object
        period (int): size of the moving period
        column (str): column name to calculate

    Returns:
        Tuple[np.ndarray, int]: the numpy ndarray object,
        and the period offset the indicator needs
    """

    return calc_ma(
        df.get_column(column)[s].to_numpy(),
        period
    ), period


ma_args = [
    # parameter setting for `period`
    arg_period,
    # setting for `column`
    (
        # The default value of the second parameter
        'close',
        # If the command use the default value,
        # then it will skip validating
        column_enums
    )
]

COMMANDS['ma'] = (
    CommandPreset(ma, ma_args),
    None,
    None
)


# ema
# ----------------------------------------------------

def ema(df, s, period, column) -> ReturnType:
    """Gets Exponential Moving Average
    """

    return calc_ewma(
        df.get_column(column)[s].to_numpy(),
        period
    ), period


COMMANDS['ema'] = (
    CommandPreset(ema, ma_args),
    None,
    None
)


# macd
# ----------------------------------------------------

def macd(df, s, fast_period, slow_period) -> ReturnType:
    fast = df.exec(f'ema:{fast_period},close', False)[s]
    slow = df.exec(f'ema:{slow_period},close', False)[s]

    return fast - slow, fast_period


def macd_signal(df, s, fast_period, slow_period, signal_period) -> ReturnType:
    macd = df.exec(f'macd:{fast_period},{slow_period}')[s]

    return calc_ewma(macd, signal_period), fast_period


MACD_HISTOGRAM_TIMES = 2.0


def macd_histogram(
    df,
    s,
    fast_period,
    slow_period,
    signal_period
) -> ReturnType:
    macd = df.exec(f'macd:{fast_period},{slow_period}')[s]
    macd_s = df.exec(
        f'macd.signal:{fast_period},{slow_period},{signal_period}'
    )[s]

    return MACD_HISTOGRAM_TIMES * (macd - macd_s), fast_period


macd_args = [
    # Fast period
    (12, period_to_int),
    # Slow period
    (26, period_to_int)
]

macd_args_all = [
    *macd_args,
    (9, period_to_int)
]

COMMANDS['macd'] = (  # type: ignore
    CommandPreset(
        macd,
        macd_args
    ),
    dict(
        signal=CommandPreset(macd_signal, macd_args_all),
        histogram=CommandPreset(macd_histogram, macd_args_all)
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

def bbi(df, s, a, b, c, d) -> ReturnType:
    """Calculates BBI (Bull and Bear Index) which is the average of
    ma:3, ma:6, ma:12, ma:24 by default
    """
    return (
        df.exec(f'ma:{a}')
        + df.exec(f'ma:{b}')
        + df.exec(f'ma:{c}')
        + df.exec(f'ma:{d}')
    ) / 4, max(a, b, c, d)


COMMANDS['bbi'] = (
    CommandPreset(
        bbi,
        [
            (3, period_to_int),
            (6, period_to_int),
            (12, period_to_int),
            (24, period_to_int)
        ]
    ),
    None,
    None
)
