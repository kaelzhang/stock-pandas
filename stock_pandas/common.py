from functools import partial
import re

from pandas import DataFrame, Series
import numpy as np


def to_int(name: str, larger_than: int, value: str):
    try:
        value = int(value)
    except ValueError:
        raise ValueError(
            f'{name} must be a positive int, but got `{value}`'
        )

    if value <= larger_than:
        raise ValueError(f'{name} must be greater than {larger_than}')

    return value


period_to_int = partial(to_int, 'period', 1)
times_to_int = partial(to_int, 'times', 0)
repeat_to_int = partial(to_int, 'repeat', 0)

def create_enum(choices: list, name: str, value: str):
    if value in choices:
        return value

    choices_str = ' or '.join([f'"{choice}"' for choice in choices])

    raise ValueError(
        f'{name} should be either {choices_str}, but got `{value}`'
    )

style_enums = partial(create_enum, [
    'bullish',
    'bearish'
], 'style')


def to_direction(value: str) -> int:
    if direction == '1':
        return 1

    if direction == '-1':
        return - 1

    raise ValueError(f'direction must be `1` or `-1`, but got `{value}`')


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


def memoize(f):
    memo = {}

    def helper(x):
        if x not in memo:
            memo[x] = f(x)
        return memo[x]
    return helper


def set_stock_metas(
    target,
    aliases_map={},
    columns_info_map={},
    directives_cache={}
):
    # Use `object.__setattr__` to avoid pandas UserWarning:
    # > Pandas doesn't allow columns to be created via a new attribute name
    object.__setattr__(target, '_stock_aliases_map', aliases_map)
    object.__setattr__(target, '_stock_columns_info_map', columns_info_map)
    object.__setattr__(target, '_stock_directives_cache', directives_cache)


def copy_stock_metas(source, target):
    columns = source.columns

    aliases_map = {}
    for alias, column in source._stock_aliases_map.items():
        # TODO: if alias is in columns, something wrong happened
        # - support .iloc, loc, and other indexing and setting methods
        if column in columns:
            aliases_map[alias] = column

    columns_info_map = {}
    for column, info in source._stock_columns_info_map.items():
        if column in columns:
            columns_info_map[column] = info

    set_stock_metas(
        target,
        aliases_map,
        columns_info_map,
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


# left parentheses
PARAN_L = '('
PARAN_R = ')'
ARGS_SEPARATOR = ','

def balance(l: list, strict: bool):
    balanced = []

    pending = None

    # ['1', '( foo:1', '3', '2  )']
    for item in l:
        if pending is None:
            if item.startswith(PARAN_L):
                # '( foo:1' -> 'foo:1'
                pending = item[1:].strip()
            else:
                balanced.append(item)
        else:
            if item.endswith(PARAN_R):
                balanced.append(
                    # foo:1,3 ,                2
                    pending + ARGS_SEPARATOR + item[:- 1].strip()
                )
                pending = None
            else:
                # foo:1    ,                3
                pending += ARGS_SEPARATOR + item

    if pending is not None:
        return raise_if(
            strict,
            ValueError(f'unbalanced argument paranthesis "({pending}"')
        )

    return balanced


def split_and_balance(args_str: str, strict: bool) -> list:
    splitted = [
        a.strip() for a in args_str.split(ARGS_SEPARATOR)
    ]

    return balance(splitted, strict) if PARAN_L in args_str else splitted


def quote_arg(arg):
    arg = str(arg)

    return f'({arg})' if ARGS_SEPARATOR in arg else arg


def join_args(args: list):
    return ARGS_SEPARATOR.join([
        quote_arg(arg) for arg in args
    ])


def rolling_window(
    array: np.ndarray,
    period: int,
    fill=np.nan,
    # A stride for float is 8
    stride: int=8
) -> np.ndarray:
    """Gets an `period`-period rolling window for 1d array
    """

    array = np.append(np.repeat(fill, period - 1), array)

    return np.lib.stride_tricks.as_strided(
        array,
        shape=(len(array) - period + 1, period),
        strides=(stride, stride)
    )
