#
# Indicators to show overbought or oversold position
# ----------------------------------------------------
from functools import partial
from typing import (
    TYPE_CHECKING, Iterator
)

import numpy as np

from stock_pandas.common import (
    rolling_calc,
    period_to_int,
)

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame  # pragma: no cover

from stock_pandas.math.ma import (
    calc_smma
)

from stock_pandas.directive.command import (
    CommandDefinition,
    CommandPreset,
    CommandArg
)
from stock_pandas.directive.types import ReturnType
from .base import BUILTIN_COMMANDS

from .args import (
    arg_period,
    arg_column_high,
    arg_column_low,
)



# llv & hhv
# ----------------------------------------------------

def llv(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    column: str
) -> ReturnType:
    """Gets LLV (Lowest of Low Value)
    """

    return rolling_calc(
        df.get_column(column)[s].to_numpy(),
        period,
        min
    ), period


preset_llv = CommandPreset(llv, [
    arg_period,
    arg_column_low
])
BUILTIN_COMMANDS['llv'] = CommandDefinition(preset_llv)


def hhv(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    column: str
) -> ReturnType:
    """Gets HHV (Highest of High Value)
    """

    return rolling_calc(
        df.get_column(column)[s].to_numpy(),
        period,
        max
    ), period


preset_hhv = CommandPreset(hhv, [
    arg_period,
    arg_column_high
])
BUILTIN_COMMANDS['hhv'] = CommandDefinition(preset_hhv)


# Donchian Channel
# ref: https://en.wikipedia.org/wiki/Donchian_channel

def donchian(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    hhv_column: str,
    llv_column: str
) -> ReturnType:
    """Gets Donchian Channel
    """

    hhv = df.exec(f'hhv:{period},{hhv_column}')[s]
    llv = df.exec(f'llv:{period},{llv_column}')[s]

    return (hhv + llv) / 2, period


BUILTIN_COMMANDS['donchian'] = CommandDefinition(
    CommandPreset(
        donchian,
        [
            arg_period,
            arg_column_high,
            arg_column_low
        ]
    ),
    dict(
        upper=preset_hhv,
        lower=preset_llv
    ),
    dict(
        u='upper',
        l='lower',
        middle=None
    )
)


# rsv
# ----------------------------------------------------

def rsv(
    column_low: str,
    column_high: str,
    df: 'StockDataFrame',
    s: slice,
    period: int
) -> ReturnType:
    """Gets RSV (Raw Stochastic Value)
    """

    llv = df.exec(f'llv:{period},{column_low}')[s]
    hhv = df.exec(f'hhv:{period},{column_high}')[s]

    v = (
        (df.get_column('close')[s] - llv) / (hhv - llv)
    ).fillna(0).astype('float64') * 100

    return v.to_numpy(), period


BUILTIN_COMMANDS['rsv'] = CommandDefinition(
    CommandPreset(
        partial[ReturnType](rsv, 'low', 'high'),
        [arg_period]
    )
)


# kdj
# ----------------------------------------------------

KDJ_WEIGHT_K = 3.0
KDJ_WEIGHT_D = 2.0


def ewma(
    array: np.ndarray,
    period: int,
    init: float
) -> Iterator[float]:
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
    df: 'StockDataFrame',
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
    df: 'StockDataFrame',
    s: slice,
    period_rsv: int,
    period_k: int,
    period_d: int,
    init: float
) -> ReturnType:
    k = df.exec(f'{base}.k:{period_rsv},{period_k},{init}')[s]

    return np.fromiter(ewma(k, period_d, init), float), period_rsv


def kdj_j(
    base: str,
    df: 'StockDataFrame',
    s: slice,
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


arg_period_k = CommandArg(3, period_to_int)
args_kdj_common = [
    CommandArg(9, period_to_int),
    arg_period_k
]
arg_init = CommandArg(50., init_to_float)

args_k =[
    *args_kdj_common,
    arg_init
]

# The default args for KDJ is 9, 3, 3, 50.
args_dj = [
    *args_kdj_common,
    arg_period_k,
    arg_init
]

BUILTIN_COMMANDS['kdj'] = CommandDefinition(
    sub_commands={
        'k': CommandPreset(
            partial(kdj_k, 'rsv'),
            args_k
        ),

        'd': CommandPreset(
            partial(kdj_d, 'kdj'),
            args_dj
        ),

        'j': CommandPreset(
            partial(kdj_j, 'kdj'),
            args_dj
        )
    }
)


# rsi
# ----------------------------------------------------

def rsi(df: 'StockDataFrame', _: slice, period: int) -> ReturnType:
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


BUILTIN_COMMANDS['rsi'] = CommandDefinition(
    CommandPreset(
        rsi,
        [arg_period]
    )
)


# kdjc
# ----------------------------------------------------

BUILTIN_COMMANDS['rsvc'] = CommandDefinition(
    CommandPreset(
        partial(rsv, 'close', 'close'),
        [arg_period]
    )
)

BUILTIN_COMMANDS['kdjc'] = CommandDefinition(
    sub_commands={
        'k': CommandPreset(
            partial(kdj_k, 'rsvc'),
            args_k
        ),
        'd': CommandPreset(
            partial(kdj_d, 'kdjc'),
            args_dj
        ),
        'j': CommandPreset(
            partial(kdj_j, 'kdjc'),
            args_dj
        )
    }
)
