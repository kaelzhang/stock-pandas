#
# Dynamic support and resistance indicators
# ----------------------------------------------------

from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from stock_pandas.common import (
    period_to_int,
    times_to_float,
    rolling_calc
)

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame  # pragma: no cover

from stock_pandas.directive.command import (
    CommandDefinition,
    CommandPreset,
    CommandArg,
)
from stock_pandas.directive.types import ReturnType
from .base import BUILTIN_COMMANDS

from .args import (
    arg_column_close
)

# boll
# ----------------------------------------------------

def boll(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    column: str
) -> ReturnType:
    """Gets the mid band of bollinger bands
    """
    return df.exec(f'ma:{period},{column}')[s], period


def boll_band(
    upper: bool,
    df: 'StockDataFrame',
    s: slice,
    period: int,
    times: float,
    column: str
) -> ReturnType:
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


arg_boll_period = CommandArg(20, period_to_int)
args_boll = [
    arg_boll_period,
    arg_column_close
]
args_boll_band = [
    arg_boll_period,
    CommandArg(2., times_to_float),
    arg_column_close
]

BUILTIN_COMMANDS['boll'] = CommandDefinition(
    CommandPreset(boll, args_boll),
    dict(
        upper=CommandPreset(
            partial(boll_band, True),
            args_boll_band
        ),
        lower=CommandPreset(
            partial(boll_band, False),
            args_boll_band
        ),
    ),
    dict(
        u='upper',  # noqa
        l='lower'   # noqa
    )
)


def bbw(
    df: 'StockDataFrame',
    s: slice,
    period: int,
    column: str
) -> ReturnType:
    """Gets the width of bollinger bands
    """

    prices = df.get_column(column)[s].to_numpy()
    ma = df.exec(f'ma:{period},{column}')[s]
    mstd = rolling_calc(
        prices,
        period,
        np.std
    )

    return np.divide(
        np.multiply(4, mstd),
        ma
    ), period


BUILTIN_COMMANDS['bbw'] = CommandDefinition(
    CommandPreset(bbw, args_boll)
)


# def vol(df, s: slice, period: int) -> ReturnType:
#     """Gets the volatility of the stock
#     """

#     # return df.get_column('volume')[s].to_numpy(), period
