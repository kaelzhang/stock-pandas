from functools import partial
from pandas import DataFrame, Series
import numpy as np


def to_int(name: str, value: str):
    try:
        value = int(value)
    except ValueError:
        raise ValueError(
            f'{name} must be a positive int, but got `{value}`'
        )

    if value <= 0:
        raise IndexError(f'{name} must be greater than 0')

    return value


period_to_int = partial(to_int, 'period')
times_to_int = partial(to_int, 'times')

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


def ensure_return_type(cls, method):
    def helper(self, *args, **kwargs):
        ret = getattr(super(cls, self), method)(*args, **kwargs)

        if isinstance(ret, DataFrame):
            return self._ensure_stock_type(ret)

        return ret

    helper.__doc__ = getattr(DataFrame, method).__doc__

    setattr(cls, method, helper)


def compare_cross(left, right):
    less = right < left

    # matrix or vector of all False value
    cross = np.zeros_like(less)

    if len(cross) > 1:
        # Find cross
        cross[1:] = np.diff(less)

    return cross, less


def is_not_nan(subject):
    if isinstance(subject, Series):
        subject = subject.values

    return ~ np.isnan(subject)
