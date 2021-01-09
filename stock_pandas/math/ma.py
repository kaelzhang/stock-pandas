from stock_pandas.common import rolling_calc
from ._lib import ewma

import numpy as np


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

    return ewma(
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


def calc_smma(
    array: np.ndarray,
    period: int
) -> np.ndarray:
    """Calculates Smoothed Moving Average(Modified Moving Average)
    https://en.wikipedia.org/wiki/Moving_average#Modified_moving_average

    >  SMMA is an EWMA, with `alpha = 1 / N`

    1. / period = 1. / (1. + com)
    """

    return ewma(
        array.astype(float),
        period - 1.,
        1,
        0,
        period
    )


def calc_ma(
    array: np.ndarray,
    period: int
) -> np.ndarray:
    """Calculates N-period Simple Moving Average
    """

    return rolling_calc(array, period, np.mean)
