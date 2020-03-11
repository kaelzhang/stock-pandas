from functools import partial

import numpy as np
from pandas import Series

from .common import (
    period_to_int,
    times_to_int,
    repeat_to_int,
    style_enums,

    to_direction,
    is_valid_stat_column,
    rolling_window
)


class CommandPreset:
    def __init__(
        self,
        formula=None,
        args=None,
        subs_map=None,
        sub_aliases_map=None
    ):
        self.formula = formula
        self.args = args
        self.subs_map = subs_map
        self.sub_aliases_map = sub_aliases_map


COMMANDS = {}


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

    return df[column][s].rolling(
        min_periods=period,
        window=period,
        center=False
    ).mean(), period


arg_period = (
    # Default value for the first argument,
    # `None` indicates that it is not an optional argument
    None,
    # Validator and setter for the first argument.
    # The function could throw
    period_to_int
)

ma_args = [
    # period
    arg_period,
    # column
    (
        'close',
        # If the command use the default value,
        # then it will skip validating
        is_valid_stat_column
    )
]

COMMANDS['ma'] = CommandPreset(ma, ma_args)


def smma(df, s, period, column):
    """Gets Smoothed Moving Average
    """

    return df[column][s].ewm(
        min_periods=period,
        ignore_na=False,
        alpha=1.0 / period,
        adjust=True
    ).mean().to_numpy(), period


COMMANDS['smma'] = CommandPreset(smma, ma_args)


def calc_ema(series, period) -> np.ndarray:
    return series.ewm(
        min_periods=period,
        ignore_na=False,
        span=period,
        adjust=True
    ).mean().to_numpy()


def ema(df, s, period, column):
    """Gets Exponential Moving Average
    """

    return calc_ema(df[column][s], period), period


COMMANDS['ema'] = CommandPreset(ema, ma_args)


def mstd(df, s, period, column):
    """Gets moving standard deviation

    Args the same as `ma`

    Returns:
        Tuple[pandas.Series, int]
    """

    return df[column][s].rolling(
        min_periods=period,
        window=period,
        center=False
    ).std().to_numpy(), period


COMMANDS['mstd'] = CommandPreset(
    mstd,
    [
        arg_period,
        ('close', is_valid_stat_column)
    ]
)


def boll(df, s, period, column):
    """Gets the mid band of bollinger bands
    """
    return df.calc(f'ma:{period},{column}')[s], period


def boll_band(upper: bool, df, s, period, times, column):
    """Gets the upper band or the lower band of bolinger bands

    Args:
        upper (bool): Get the upper band if True else the lower band
    """
    ma = df.calc(f'ma:{period},{column}')[s]
    mstd = df.calc(f'mstd:{period},{column}')[s]

    ma = list(map(np.float64, ma))
    mstd = list(map(np.float64, mstd))

    if upper:
        return np.add(ma, np.multiply(times, mstd)), period
    else:
        return np.subtract(ma, np.multiply(times, mstd)), period


boll_band_args = [
    (20, period_to_int),
    (2, times_to_int),
    ('close', is_valid_stat_column)
]

COMMANDS['boll'] = CommandPreset(
    boll,
    [
        (20, period_to_int),
        ('close', is_valid_stat_column)
    ],
    dict(
        upper=CommandPreset(
            partial(boll_band, True),
            boll_band_args
        ),
        lower=CommandPreset(
            partial(boll_band, False),
            boll_band_args
        ),
    ),
    dict(
        u='upper',  # noqa
        l='lower'   # noqa
    )
)


def column(df, s, column):
    """Gets the series of the column named `column`
    """

    return df.loc[s, column].to_numpy(), 0


COMMANDS['column'] = CommandPreset(
    column,
    [(None, None)]
)


def rsv(df, s, period):
    """Gets RSV (Raw Stochastic Value)
    """

    # Lowest Low Value
    llv = df['low'][s].rolling(
        min_periods=period,
        window=period,
        center=False
    ).min()

    # Highest High Value
    hhv = df['high'][s].rolling(
        min_periods=period,
        window=period,
        center=False
    ).max()

    v = (
        (df['close'][s] - llv) / (hhv - llv)
    ).fillna(0).astype('float64') * 100

    return v.to_numpy(), period


COMMANDS['rsv'] = CommandPreset(
    rsv,
    [arg_period]
)


KDJ_WEIGHT_K = 3.0
KDJ_WEIGHT_D = 2.0
KDJ_WEIGHT_BASE = KDJ_WEIGHT_D / KDJ_WEIGHT_K
KDJ_WEIGHT_INCREASE = 1.0 / KDJ_WEIGHT_K


def kd(series):
    # If there is no value k or value d of the previous day,
    # then use 50.0
    k = 50.0

    for i in series:
        k = KDJ_WEIGHT_BASE * k + KDJ_WEIGHT_INCREASE * i
        yield k


def kdj_k(df, s, period):
    """Gets KDJ K
    """

    rsv = df.calc(f'rsv:{period}')[s]

    return np.fromiter(kd(rsv), float), period


def kdj_d(df, s, period):
    k = df.calc(f'kdj.k:{period}')[s]

    return np.fromiter(kd(k), float), period


def kdj_j(df, s, period):
    k = df.calc(f'kdj.k:{period}')[s]
    d = df.calc(f'kdj.d:{period}')[s]

    return KDJ_WEIGHT_K * k - KDJ_WEIGHT_D * d, period


kdj_arg_period = [(9, period_to_int)]

COMMANDS['kdj'] = CommandPreset(
    # We must specify sub command for kdj, such as
    # 'kdj.k'
    subs_map=dict(
        k=CommandPreset(
            kdj_k,
            kdj_arg_period
        ),

        d=CommandPreset(
            kdj_d,
            kdj_arg_period
        ),

        j=CommandPreset(
            kdj_j,
            kdj_arg_period
        )
    )
)


def macd(df, s, fast_period, slow_period):
    fast = df.calc(f'ema:{fast_period},close', False)[s]
    slow = df.calc(f'ema:{slow_period},close', False)[s]

    return fast - slow, fast_period


def macd_signal(df, s, fast_period, slow_period, signal_period):
    macd = df.calc(f'macd:{fast_period},{slow_period}')[s]

    return calc_ema(macd, signal_period), fast_period


def macd_histogram(df, s, fast_period, slow_period, signal_period):
    macd = df.calc(f'macd:{fast_period},{slow_period}')[s]
    macd_s = df.calc(
        f'macd.signal:{fast_period},{slow_period},{signal_period}'
    )[s]

    return macd - macd_s, fast_period


macd_args = [
    # Fast period
    (26, period_to_int),
    # Slow period
    (12, period_to_int)
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


POSITIVE_INFINITY = float('inf')
NEGATIVE_INFINITY = float('-inf')

def check_increase(direction, current, ndarray):
    for value in ndarray:
        if np.isnan(value):
            return False

        if (value - current) * direction > 0:
            current = value
        else:
            return False

    return True


def increase(df, s, on_what: str, repeat: int, direction: int):
    period = repeat + 1

    current = NEGATIVE_INFINITY if direction == 1 else POSITIVE_INFINITY
    compare = partial(check_increase, direction, current)

    return np.apply_along_axis(
        compare,
        1,
        rolling_window(df.calc(on_what)[s], period)
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
    result = df.calc(command_str)[s]

    return result if repeat == 1 else np.apply_along_axis(
        np.all,
        1,
        rolling_window(result, repeat, False, 1)
    ), repeat

COMMANDS['repeat'] = CommandPreset(
    repeat,
    [
        (None, None),
        (1, repeat_to_int)
    ]
)
