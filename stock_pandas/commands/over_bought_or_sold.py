#
# Indicators to show overbought or oversold position
# ----------------------------------------------------
from typing import (
    Iterator
)

import numpy as np

from stock_pandas.common import (
    rolling_calc,
    period_to_int,
)

from stock_pandas.math.ma import (
    calc_smma
)

from stock_pandas.directive.command import CommandDefinition
from stock_pandas.directive.types import (
    ReturnType,
    CommandArgInputType,
    CommandPreset,
    CommandArg
)
from .base import BUILTIN_COMMANDS

from .common import (
    arg_period,
    lookback_period,
    lookback_a_lot,
    create_series_args,
    series_close
)

# Try to import Rust implementations for better performance
try:
    from stock_pandas_rs import (
        calc_llv as _rs_llv,
        calc_hhv as _rs_hhv,
        calc_rsv as _rs_rsv,
        calc_kdj_k as _rs_kdj_k,
        calc_kdj_d as _rs_kdj_d,
        calc_kdj_j as _rs_kdj_j,
        calc_rsi as _rs_rsi,
        calc_donchian as _rs_donchian
    )
    _USE_RUST = True
except ImportError:
    _USE_RUST = False


# llv & hhv
# ----------------------------------------------------

def llv(
    period: int,
    column: ReturnType
) -> ReturnType:
    """Gets LLV (Lowest of Low Value)
    """
    if _USE_RUST:
        return np.asarray(_rs_llv(column.astype(float), period))

    return rolling_calc(column, period, min)


preset_llv = CommandPreset(
    formula=llv,
    lookback=lookback_period,
    args=[arg_period],
    series=create_series_args(['low'])
)
BUILTIN_COMMANDS['llv'] = CommandDefinition(preset_llv)


def hhv(
    period: int,
    column: ReturnType
) -> ReturnType:
    """Gets HHV (Highest of High Value)
    """
    if _USE_RUST:
        return np.asarray(_rs_hhv(column.astype(float), period))

    return rolling_calc(column, period, max)


preset_hhv = CommandPreset(
    formula=hhv,
    lookback=lookback_period,
    args=[arg_period],
    series=create_series_args(['high'])
)
BUILTIN_COMMANDS['hhv'] = CommandDefinition(preset_hhv)


# Donchian Channel
# ref: https://en.wikipedia.org/wiki/Donchian_channel

def donchian(
    period: int,
    hhv_series: ReturnType,
    llv_series: ReturnType
) -> ReturnType:
    """Gets Donchian Channel
    """
    if _USE_RUST:
        return np.asarray(_rs_donchian(
            hhv_series.astype(float),
            llv_series.astype(float),
            period
        ))

    return (hhv(period, hhv_series) + llv(period, llv_series)) / 2


BUILTIN_COMMANDS['donchian'] = CommandDefinition(
    CommandPreset(
        formula=donchian,
        lookback=lookback_period,
        args=[arg_period],
        series=create_series_args(['high', 'low'])
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
    period: int,
    high_series: ReturnType,
    low_series: ReturnType,
    close_series: ReturnType
) -> ReturnType:
    """Gets RSV (Raw Stochastic Value)
    """
    if _USE_RUST:
        return np.asarray(_rs_rsv(
            high_series.astype(float),
            low_series.astype(float),
            close_series.astype(float),
            period
        ))

    llv_series = llv(period, low_series)
    hhv_series = hhv(period, high_series)

    v = (close_series - llv_series) / (hhv_series - llv_series)

    return np.nan_to_num(
        v,
        nan=0.0, posinf=0.0, neginf=0.0
    ).astype(np.float64) * 100


series_rsv = create_series_args(['high', 'low', 'close'])

BUILTIN_COMMANDS['rsv'] = CommandDefinition(
    CommandPreset(
        formula=rsv,
        lookback=lookback_period,
        args=[arg_period],
        series=series_rsv
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
    period_rsv: int,
    period_k: int,
    init: float,
    high_series: ReturnType,
    low_series: ReturnType,
    close_series: ReturnType
) -> ReturnType:
    """Gets KDJ K
    """
    if _USE_RUST:
        return np.asarray(_rs_kdj_k(
            high_series.astype(float),
            low_series.astype(float),
            close_series.astype(float),
            period_rsv,
            period_k,
            init
        ))

    rsv_series = rsv(period_rsv, high_series, low_series, close_series)

    return np.fromiter(ewma(rsv_series, period_k, init), float)


def kdj_d(
    period_rsv: int,
    period_k: int,
    period_d: int,
    init: float,
    high_series: ReturnType,
    low_series: ReturnType,
    close_series: ReturnType
) -> ReturnType:
    if _USE_RUST:
        return np.asarray(_rs_kdj_d(
            high_series.astype(float),
            low_series.astype(float),
            close_series.astype(float),
            period_rsv,
            period_k,
            period_d,
            init
        ))

    k_series = kdj_k(
        period_rsv, period_k, init,
        high_series, low_series, close_series
    )

    return np.fromiter(ewma(k_series, period_d, init), float)


def kdj_j(
    period_rsv: int,
    period_k: int,
    period_d: int,
    init: float,
    high_series: ReturnType,
    low_series: ReturnType,
    close_series: ReturnType
) -> ReturnType:
    if _USE_RUST:
        return np.asarray(_rs_kdj_j(
            high_series.astype(float),
            low_series.astype(float),
            close_series.astype(float),
            period_rsv,
            period_k,
            period_d,
            init
        ))

    k_series = kdj_k(
        period_rsv, period_k, init,
        high_series, low_series, close_series
    )
    d_series = kdj_d(
        period_rsv, period_k, period_d, init,
        high_series, low_series, close_series
    )

    return KDJ_WEIGHT_K * k_series - KDJ_WEIGHT_D * d_series


def init_to_float(raw_value: CommandArgInputType) -> float:
    try:
        value = float(raw_value)
    except Exception:
        raise ValueError(
            f'init_value must be a float, but got `{raw_value}`'
        )

    if value < 0. or value > 100.:
        raise ValueError(
            f'init_value must be in between 0 and 100, but got `{raw_value}`'
        )

    return value


arg_period_k = CommandArg(3, period_to_int)
args_kdj_common = [
    # period of rsv
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
            formula=kdj_k,
            # KDJ needs more lookback to warm up ewma
            lookback=lookback_a_lot,
            args=args_k,
            series=series_rsv
        ),

        'd': CommandPreset(
            formula=kdj_d,
            lookback=lookback_a_lot,
            args=args_dj,
            series=series_rsv
        ),

        'j': CommandPreset(
            formula=kdj_j,
            lookback=lookback_a_lot,
            args=args_dj,
            series=series_rsv
        )
    }
)


# rsi
# ----------------------------------------------------

def rsi(period: int, close_series: ReturnType) -> ReturnType:
    """Calculates N-period RSI (Relative Strength Index)

    https://en.wikipedia.org/wiki/Relative_strength_index
    """
    if _USE_RUST:
        return np.asarray(_rs_rsi(close_series.astype(float), period))

    delta = np.diff(close_series, prepend=np.nan)

    # gain
    U = (np.absolute(delta) + delta) / 2.
    # loss
    D = (np.absolute(delta) - delta) / 2.

    smma_u = calc_smma(U, period)
    smma_d = calc_smma(D, period)

    return 100 - 100 / (1. + smma_u / smma_d)


def lookback_rsi(period: int) -> int:
    # period - 1 + 1 (diff)
    return period


BUILTIN_COMMANDS['rsi'] = CommandDefinition(
    CommandPreset(
        formula=rsi,
        lookback=lookback_rsi,
        args=[arg_period],
        series=series_close
    )
)
