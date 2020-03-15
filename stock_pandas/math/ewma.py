import pandas._libs.window.aggregations as window_aggregations
import numpy as np

_ewma = window_aggregations.ewma

def ewma(
    array: np.ndarray,
    period: int,
    min_periods: int
) -> np.ndarray:
    return _ewma(
        array.astype(float),
        1.0 / period,
        # we always use adjust=True in ewma
        1,
        # ignore_na=False
        0,
        min_periods
    )
