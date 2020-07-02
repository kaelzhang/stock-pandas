#
# Dynamic support and resistance indicators
# ----------------------------------------------------

from functools import partial
import numpy as np

from .base import (
    COMMANDS,
    CommandPreset,
    ReturnType
)

from stock_pandas.common import (
    period_to_int,
    times_to_float,
    column_enums,

    rolling_calc
)


# boll
# ----------------------------------------------------

def boll(df, s, period, column) -> ReturnType:
    """Gets the mid band of bollinger bands
    """
    return df.exec(f'ma:{period},{column}')[s], period


def boll_band(upper: bool, df, s, period, times, column) -> ReturnType:
    """Gets the upper band or the lower band of bolinger bands

    Args:
        upper (bool): Get the upper band if True else the lower band
    """

    prices = df.get_column(column)[s].to_numpy()

    ma = df.exec(f'ma:{period},{column}')[s]
    mstd = rolling_calc(
        prices,
        period,
        np.std
    )

    if upper:
        return np.add(ma, np.multiply(times, mstd)), period
    else:
        return np.subtract(ma, np.multiply(times, mstd)), period


boll_band_args = [
    (20, period_to_int),
    (2., times_to_float),
    ('close', column_enums)
]

COMMANDS['boll'] = (  # type: ignore
    CommandPreset(
        boll,
        [
            (20, period_to_int),
            ('close', column_enums)
        ]
    ),
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
