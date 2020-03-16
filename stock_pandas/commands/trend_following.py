#
# Trend-following momentum indicators
# ----------------------------------------------------

from .base import (
    COMMANDS,
    CommandPreset,

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


def ma(df, s, period, column):
    """Gets simple moving average

    Args:
        df (DataFrame): data
        s (slice): the slice object
        period (int): size of the moving period
        column (str): column name to calculate

    Returns:
        Tuple[pandas.Series, int]: the pandas Series object,
        and the period offset the indicator needs
    """

    return calc_ma(
        df[column][s].to_numpy(),
        period
    ), period


ma_args = [
    # period
    arg_period,
    # column
    (
        'close',
        # If the command use the default value,
        # then it will skip validating
        column_enums
    )
]

COMMANDS['ma'] = CommandPreset(ma, ma_args)


# ema
# ----------------------------------------------------

def ema(df, s, period, column):
    """Gets Exponential Moving Average
    """

    return calc_ewma(
        df[column][s].to_numpy(),
        period
    ), period


COMMANDS['ema'] = CommandPreset(ema, ma_args)


# macd
# ----------------------------------------------------

def macd(df, s, fast_period, slow_period):
    fast = df.exec(f'ema:{fast_period},close', False)[s]
    slow = df.exec(f'ema:{slow_period},close', False)[s]

    return fast - slow, fast_period


def macd_signal(df, s, fast_period, slow_period, signal_period):
    macd = df.exec(f'macd:{fast_period},{slow_period}')[s]

    return calc_ewma(macd, signal_period), fast_period


MACD_HISTOGRAM_TIMES = 2.0


def macd_histogram(df, s, fast_period, slow_period, signal_period):
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

COMMANDS['macd'] = CommandPreset(
    macd,
    macd_args,
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

def bbi(df, s, a, b, c, d):
    """Calculates BBI (Bull and Bear Index) which is the average of
    ma:3, ma:6, ma:12, ma:24 by default
    """
    return (
        df.exec(f'ma:{a}')
        + df.exec(f'ma:{b}')
        + df.exec(f'ma:{c}')
        + df.exec(f'ma:{d}')
    ) / 4, max(a, b, c, d)


COMMANDS['bbi'] = CommandPreset(
    bbi,
    [
        (3, period_to_int),
        (6, period_to_int),
        (12, period_to_int),
        (24, period_to_int)
    ]
)
