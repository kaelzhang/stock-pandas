def period_to_int(period: str):
    try:
        period = int(period)
    except ValueError:
        raise ValueError(
            'period must be a positive int, but got `{}`'.format(period)
        )

    if period <= 0:
        raise IndexError('period must be greater than 0')

    return period

COLUMNS = [
    'open',
    'high',
    'low',
    'close'
]

def is_ohlc_column(column: str):
    return column in COLUMNS


def is_valid_stat_column(column: str):
    if is_ohlc_column(column):
        return column

    raise ValueError(
        f'"{column}" is not a valid column for statistics'
    )


def join_list(l: list, separator: str):
    return separator.join([str(x) for x in l])
