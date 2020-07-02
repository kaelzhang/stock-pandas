#
# Indicators to show overbought or oversold position
# ----------------------------------------------------
from functools import partial
import numpy as np

from .base import (
    COMMANDS,
    CommandPreset,
    ReturnType,

    arg_period
)

from stock_pandas.common import (
    rolling_calc,
    period_to_int,
    column_enums
)

from stock_pandas.math.ma import (
    calc_smma
)


# llv & hhv
# ----------------------------------------------------

def llv(df, s, period, column) -> ReturnType:
    """Gets LLV (Lowest of Low Value)
    """

    return rolling_calc(
        df.get_column(column)[s].to_numpy(),
        period,
        min
    ), period


COMMANDS['llv'] = (
    CommandPreset(
        llv,
        [
            arg_period,
            ('low', column_enums)
        ]
    ),
    None,
    None
)


def hhv(df, s, period, column) -> ReturnType:
    """Gets HHV (Highest of High Value)
    """

    return rolling_calc(
        df.get_column(column)[s].to_numpy(),
        period,
        max
    ), period


COMMANDS['hhv'] = (
    CommandPreset(
        hhv,
        [
            arg_period,
            ('high', column_enums)
        ]
    ),
    None,
    None
)


# rsv
# ----------------------------------------------------

def rsv(column_low, column_high, df, s, period) -> ReturnType:
    """Gets RSV (Raw Stochastic Value)
    """

    llv = df.exec(f'llv:{period},{column_low}')[s]
    hhv = df.exec(f'hhv:{period},{column_high}')[s]

    v = (
        (df.get_column('close')[s] - llv) / (hhv - llv)
    ).fillna(0).astype('float64') * 100

    return v.to_numpy(), period


COMMANDS['rsv'] = (
    CommandPreset(
        partial(rsv, 'low', 'high'),
        [arg_period]
    ),
    None,
    None
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


def kdj_k(
    base: str,
    df,
    s: slice,
    period_rsv: int,
    period_k: int,
    init: float
) -> ReturnType:
    """Gets KDJ K
    """

    rsv = df.exec(f'{base}:{period_rsv}')[s]

    return np.fromiter(ewma(rsv, period_k, init), float), period_rsv


def kdj_d(
    base: str,
    df,
    s,
    period_rsv: int,
    period_k: int,
    period_d: int,
    init: float
) -> ReturnType:
    k = df.exec(f'{base}.k:{period_rsv},{period_k},{init}')[s]

    return np.fromiter(ewma(k, period_d, init), float), period_rsv


def kdj_j(
    base: str,
    df,
    s,
    period_rsv: int,
    period_k: int,
    period_d: int,
    init: float
) -> ReturnType:
    k = df.exec(f'{base}.k:{period_rsv},{period_k},{init}')[s]
    d = df.exec(f'{base}.d:{period_rsv},{period_k},{period_d},{init}')[s]

    return KDJ_WEIGHT_K * k - KDJ_WEIGHT_D * d, period_rsv


def init_to_float(raw_value: str) -> float:
    try:
        value = float(raw_value)
    except Exception:
        raise ValueError(
            f'init_value must be a float, but got `{raw_value}`'
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


COMMANDS['kdj'] = (
    None,
    # We must specify sub command for kdj, such as
    # 'kdj.k'
    dict(
        k=CommandPreset(
            partial(kdj_k, 'rsv'),
            args_k
        ),

        d=CommandPreset(
            partial(kdj_d, 'kdj'),
            args_dj
        ),

        j=CommandPreset(
            partial(kdj_j, 'kdj'),
            args_dj
        )
    ),
    None
)


# rsi
# ----------------------------------------------------

def rsi(df, s, period) -> ReturnType:
    """Calculates N-period RSI (Relative Strength Index)

    https://en.wikipedia.org/wiki/Relative_strength_index
    """

    delta = df.get_column('close').diff().to_numpy()

    # gain
    U = (np.absolute(delta) + delta) / 2.
    # loss
    D = (np.absolute(delta) - delta) / 2.

    smma_u = calc_smma(U, period)
    smma_d = calc_smma(D, period)

    return 100 - 100 / (1. + smma_u / smma_d), period


COMMANDS['rsi'] = (
    CommandPreset(
        rsi,
        [arg_period]
    ),
    None,
    None
)
