import pandas._libs.window.aggregations as window_aggregations
import numpy as np

_ewma = window_aggregations.ewma

def ewma(
    array: np.ndarray,
    period: int,
    min_periods: int
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

    return _ewma(
        # Sometimes, the series in a DataFrame is of int type
        array.astype(float),
        (period - 1.) / 2.,
        # we always use adjust=True in ewma
        1,
        # ignore_na=False
        0,
        min_periods
    )
