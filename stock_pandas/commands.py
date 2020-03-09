from functools import partial
import numpy as np

from .common import (
    period_to_int, times_to_int,
    is_valid_stat_column
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
    """Gets
    """

    return df[column][s].ewm(
        min_periods=period,
        ignore_na=False,
        alpha=1.0 / period,
        adjust=True
    ).mean(), period

COMMANDS['smma'] = CommandPreset(smma, ma_args)


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
    ).std(), period


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

    return df.loc[s, column], 0


COMMANDS['column'] = CommandPreset(
    column,
    [(None, None)]
)



def rsv(df, s, period):
    """Gets RSV (Raw Stochastic Value)
    """

    # Lowest Low Value
    llv = df['low'][s].rolling(
        min_periods=1,
        window=period,
        center=False
    ).min()

    # Highest High Value
    hhv = df['high'][s].rolling(
        min_periods=1,
        window=period,
        center=False
    ).max()

    v = (
        (df['close'][s] - llv) / (hhv - llv)
    ).fillna(0).astype('float64') * 100

    return v, period

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

    for i in KDJ_WEIGHT_INCREASE * series:
        k = KDJ_WEIGHT_BASE * k + i
        yield k


def kdj_k(df, s, period):
    """Gets KDJ K
    """

    return list(kd(df[f'rsv:{period}'][s])), period


def kdj_d(df, s, period):
    return list(kd(df[f'kdj.k:{period}'][s])), period


def kdj_j(df, s, period):
    k = df[f'kdj.k:{period}'][s]
    d = df[f'kdj.d:{period}'][s]
    return KDJ_WEIGHT_K * k - KDJ_WEIGHT_D * d, period


COMMANDS['kdj'] = CommandPreset(
    # We must specify sub command for kdj, such as
    # 'kdj.k'
    subs_map=dict(
        k=CommandPreset(
            kdj_k,
            [(9, period_to_int)]
        ),

        d=CommandPreset(
            kdj_d,
            [(9, period_to_int)]
        ),

        j=CommandPreset(
            kdj_j,
            [(9, period_to_int)]
        )
    )
)


