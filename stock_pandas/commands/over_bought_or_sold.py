#
# Indicators to show overbought or oversold position
# ----------------------------------------------------
import numpy as np

from .base import (
    COMMANDS,
    CommandPreset,

    arg_period
)

from stock_pandas.common import (
    period_to_int
)

from stock_pandas.math.ma import (
    calc_smma
)


# rsv
# ----------------------------------------------------

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


# kdj
# ----------------------------------------------------

KDJ_WEIGHT_K = 3.0
KDJ_WEIGHT_D = 2.0


def ewma(
    array: np.ndarray,
    period: int,
    init: float
):
    """Exponentially weighted moving average
    https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

    with
    - init value as `50.0`
    - alpha as `1 / period`
    """

    # If there is no value k or value d of the previous day,
    # then use 50.0
    k = init
    alpha = 1. / period
    base = 1 - alpha

    for i in array:
        k = base * k + alpha * i
        yield k


def kdj_k(df, s, period_rsv, period_k, init):
    """Gets KDJ K
    """

    rsv = df.exec(f'rsv:{period_rsv}')[s]

    return np.fromiter(ewma(rsv, period_k, init), float), period_rsv


def kdj_d(df, s, period_rsv, period_k, period_d, init):
    k = df.exec(f'kdj.k:{period_rsv},{period_k},{init}')[s]

    return np.fromiter(ewma(k, period_d, init), float), period_rsv


def kdj_j(df, s, period_rsv, period_k, period_d, init):
    k = df.exec(f'kdj.k:{period_rsv},{period_k},{init}')[s]
    d = df.exec(f'kdj.d:{period_rsv},{period_k},{period_d},{init}')[s]

    return KDJ_WEIGHT_K * k - KDJ_WEIGHT_D * d, period_rsv


def init_to_float(value):
    try:
        value = float(value)
    except Exception:
        raise ValueError(
            f'init_value must be a float, but got `{value}`'
        )

    if value < 0. or value > 100.:
        raise ValueError(
            f'init_value must be in between 0 and 100, but got `{value}`'
        )

    return value


arg_period_k = (3, period_to_int)
kdj_common_args = [
    (9, period_to_int),
    arg_period_k
]
arg_init = (50., init_to_float)

args_k = [
    *kdj_common_args,
    arg_init
]

# The default args for KDJ is 9, 3, 3, 50.
args_dj = [
    *kdj_common_args,
    arg_period_k,
    arg_init
]


COMMANDS['kdj'] = CommandPreset(
    # We must specify sub command for kdj, such as
    # 'kdj.k'
    subs_map=dict(
        k=CommandPreset(
            kdj_k,
            args_k
        ),

        d=CommandPreset(
            kdj_d,
            args_dj
        ),

        j=CommandPreset(
            kdj_j,
            args_dj
        )
    )
)


# rsi
# ----------------------------------------------------

def rsi(df, s, period):
    """Calculates N-period RSI (Relative Strength Index)

    https://en.wikipedia.org/wiki/Relative_strength_index
    """

    delta = df['close'].diff().to_numpy()

    # gain
    U = (np.absolute(delta) + delta) / 2.
    # loss
    D = (np.absolute(delta) - delta) / 2.

    smma_u = calc_smma(U, period)
    smma_d = calc_smma(D, period)

    return 100 - 100 / (1. + smma_u / smma_d), period


COMMANDS['rsi'] = CommandPreset(
    rsi,
    [arg_period]
)
