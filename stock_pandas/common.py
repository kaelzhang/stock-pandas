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


def memoize(f):
    memo = {}

    def helper(x):
        if x not in memo:
            memo[x] = f(x)
        return memo[x]
    return helper


def set_stock_metas(
    target,
    aliases={},
    columns={},
    directives_cache={}
):
    # Use `object.__setattr__` to avoid pandas UserWarning:
    # > Pandas doesn't allow columns to be created via a new attribute name
    object.__setattr__(target, '_stock_aliases', aliases)
    object.__setattr__(target, '_stock_columns', columns)
    object.__setattr__(target, '_stock_directives_cache', directives_cache)


def copy_stock_metas(source, target):
    set_stock_metas(
        target,
        source._stock_aliases,
        source._stock_columns,
        source._stock_directives_cache
    )

def raise_if(strict: bool, err):
    if strict:
        raise err
