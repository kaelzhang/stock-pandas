from .common import (
    period_to_int,
    is_valid_stat_column
)


class CommandPreset:
    def __init__(self, formula, args):
        self.formula = formula
        self.args = args


COMMAND_PRESETS = {}


def sma(df, s, period, column):
    """Gets simple moving average

    Args:
        df (DataFrame): data
        s (slice): the slice object
        period (int): size of the moving period
        column (str): column name to calculate

    Returns:
        pandas.Series
    """

    return df[column][s].rolling(
        min_periods=period,
        window=period,
        center=False
    ).mean(), period


COMMAND_PRESETS['sma'] = CommandPreset(
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

COMMAND_PRESETS['boll'] = True
