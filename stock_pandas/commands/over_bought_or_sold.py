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

    rsv = df.exec(f'rsv:{period}')[s]

    return np.fromiter(kd(rsv), float), period


def kdj_d(df, s, period):
    k = df.exec(f'kdj.k:{period}')[s]

    return np.fromiter(kd(k), float), period


def kdj_j(df, s, period):
    k = df.exec(f'kdj.k:{period}')[s]
    d = df.exec(f'kdj.d:{period}')[s]

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
