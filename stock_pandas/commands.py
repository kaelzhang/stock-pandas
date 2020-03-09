from functools import partial
import numpy as np

from .common import (
    period_to_int, times_to_int,
    is_valid_stat_column
)


class CommandPreset:
    def __init__(
        self,
        formula,
        args,
        subs_map=None,
        aliases_map=None
    ):
        self.formula = formula
        self.args = args
        self.subs_map = subs_map
        self.aliases_map = aliases_map


COMMANDS = {}


def sma(df, s, period, column):
    """Gets simple moving average

    Args:
        df (DataFrame): data
        s (slice): the slice object
        period (int): size of the moving period
        column (str): column name to calculate

    Returns:
        Tuple[pandas.Series, int]: the pandas Series object,
        and the period offset the indicator needs
    """

    return df[column][s].rolling(
        min_periods=period,
        window=period,
        center=False
    ).mean(), period


COMMANDS['sma'] = CommandPreset(
    # formula
    sma,
    [
        # period
        (
            # Default value for the first argument,
            # `None` indicates that it is not an optional argument
            None,
            # Validator and setter for the first argument.
            # The function could throw
            period_to_int
        ),
        # column
        (
            'close',
            # If the command use the default value,
            # then it will skip validating
            is_valid_stat_column
        )
    ]
)


def mstd(df, s, period, column):
    """Gets moving standard deviation

    Args the same as `sma`

    Returns:
        Tuple[pandas.Series, int]
    """

    return df[column][s].rolling(
        min_periods=period,
        window=period,
        center=False
    ).std(), period


COMMANDS['mstd'] = CommandPreset(
    mstd,
    [
        (None, period_to_int),
        ('close', is_valid_stat_column)
    ]
)


def boll(df, s, period, column):
    return df.calc(f'sma:{period},{column}')[s]

def boll_band(add: bool, df, s, period, times, column):
    sma = df.calc(f'sma:{period},{column}')[s]
    mstd = df.calc(f'mstd:{period},{column}')[s]

    sma = list(map(np.float64, sma))
    mstd = list(map(np.float64, mstd))

    if add:
        return np.add(sma, np.multiply(times, mstd))
    else:
        return np.subtract(sma, np.multiply(times, mstd))

boll_band_args = [
    (20, period_to_int),
    (2, times_to_int),
    ('close', is_valid_stat_column)
]

COMMANDS['boll'] = CommandPreset(
    boll,
    [
        (20, period_to_int),
        ('close', is_valid_stat_column)
    ],
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
        u='upper',
        l='lower'
    )
)
