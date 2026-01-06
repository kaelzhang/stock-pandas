"""Moving average calculations.

This module provides moving average implementations that use the Rust backend
for optimal performance, with fallback to pure Python implementations.
"""

from stock_pandas.common import rolling_calc

import numpy as np

# Try to import Rust implementation, fall back to Python if not available
try:
    from stock_pandas_rs import (
        calc_ma as _rs_calc_ma,
        calc_ewma as _rs_calc_ewma,
        calc_smma as _rs_calc_smma
    )
    _USE_RUST = True
except ImportError:
    _USE_RUST = False
    # Import the legacy Cython implementation as fallback
    try:
        from ._lib import ewma as _cython_ewma
        _USE_CYTHON = True
    except ImportError:
        _USE_CYTHON = False


def calc_ewma(
    array: np.ndarray,
    period: int
) -> np.ndarray:
    """Calculates Exponential Weighted Moving Average.

    About `_ewma::com`

    According to pandas._libs.window.aggregations.pyx,
    the ewma alpha which follows the formula:
        alpha = 1. / (1. + com)

    And for ewma:
        alpha = 2. / (1 + period)

    So:
        com = (period - 1.) / 2.
    """
    if _USE_RUST:
        return np.asarray(_rs_calc_ewma(array.astype(float), period))

    if _USE_CYTHON:
        return _cython_ewma(
            # Sometimes, the series in a DataFrame is of int type
            array.astype(float),
            (period - 1.) / 2.,
            # we always use adjust=True in ewma
            1,
            # ignore_na=False
            0,
            # For now, all calculations require `min_periods` as `period`
            period
        )

    # Pure Python fallback (slower)
    n = len(array)
    result = np.empty(n)
    result[:] = np.nan

    alpha = 2.0 / (period + 1.0)
    one_minus_alpha = 1.0 - alpha

    ewma_val = np.nan
    count = 0

    for i in range(n):
        val = float(array[i])
        if not np.isnan(val):
            count += 1
            if np.isnan(ewma_val):
                ewma_val = val
            else:
                ewma_val = alpha * val + one_minus_alpha * ewma_val

        if count >= period:
            result[i] = ewma_val

    return result


def calc_smma(
    array: np.ndarray,
    period: int
) -> np.ndarray:
    """Calculates Smoothed Moving Average(Modified Moving Average)
    https://en.wikipedia.org/wiki/Moving_average#Modified_moving_average

    >  SMMA is an EWMA, with `alpha = 1 / N`

    1. / period = 1. / (1. + com)
    """
    if _USE_RUST:
        return np.asarray(_rs_calc_smma(array.astype(float), period))

    if _USE_CYTHON:
        return _cython_ewma(
            array.astype(float),
            period - 1.,
            1,
            0,
            period
        )

    # Pure Python fallback
    n = len(array)
    result = np.empty(n)
    result[:] = np.nan

    alpha = 1.0 / period
    one_minus_alpha = 1.0 - alpha

    smma_val = np.nan
    count = 0

    for i in range(n):
        val = float(array[i])
        if not np.isnan(val):
            count += 1
            if np.isnan(smma_val):
                smma_val = val
            else:
                smma_val = alpha * val + one_minus_alpha * smma_val

        if count >= period:
            result[i] = smma_val

    return result


def calc_ma(
    array: np.ndarray,
    period: int
) -> np.ndarray:
    """Calculates N-period Simple Moving Average
    """
    if _USE_RUST:
        return np.asarray(_rs_calc_ma(array.astype(float), period))

    return rolling_calc(array, period, np.mean)
