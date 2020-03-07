from .utils import (
    period_to_int, is_valid_column
)

INDICATORS = {}


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
    period = period_to_int(period)

    return df[column][s].rolling(
        min_periods=period,
        window=period,
        center=False
    ).mean()


INDICATORS['sma'] = (
    # mutations
    sma,
    [
        (
            # Default value for the first argument,
            # `None` indicates that it is not an optional argument
            None,
            # Validator for the first argument
            period_to_int
        ),
        (
            'close',
            # If the command use the default value,
            # then it will skip validating
            is_valid_column
        )
    ]
)
