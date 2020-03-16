from functools import partial
from typing import Callable

from pandas import DataFrame
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

column_enums = partial(create_enum, [
    'open',
    'high',
    'low',
    'close'
], 'column')


def to_direction(value: str) -> int:
    if value == '1':
        return 1

    if value == '-1':
        return - 1

    raise ValueError(f'direction must be `1` or `-1`, but got `{value}`')


# A simple cache
class DirectiveCache:
    def __init__(self):
        self._store = {}

    def set(self, key: str, value):
        self._store[key] = value

    def get(self, key: str, default=None):
        return self._store.get(key, default)


def set_stock_metas(
    target,
    aliases_map={},
    columns_info_map={},
    directives_cache=DirectiveCache()
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


ARGS_SEPARATOR = ','


def join_args(args: list):
    return ARGS_SEPARATOR.join([
        str(arg) for arg in args
    ])


def rolling_window(
    array: np.ndarray,
    period: int,
    # A stride for float is 8
    stride: int = 8
) -> np.ndarray:
    """Gets an `period`-period rolling window for 1d array
    """

    return np.lib.stride_tricks.as_strided(
        array,
        shape=(len(array) - period + 1, period),
        strides=(stride, stride)
    )


def shift_and_fill(
    array: np.ndarray,
    period: int,
    fill=np.nan
) -> np.ndarray:
    """Adds items to the left of an array to meet the min periods
    """

    return np.append(np.repeat(fill, period - 1), array)


def rolling_calc(
    array: np.ndarray,
    period: int,
    func: Callable,
    fill=np.nan,
    stride: int = 8
) -> np.ndarray:
    unshifted = np.apply_along_axis(
        func,
        1,
        rolling_window(array, period, stride)
    )

    return shift_and_fill(unshifted, period, fill)


DEFAULT_ARG_VALUE = ''


def command_full_name(name, sub):
    return f'{name}.{sub}' if sub else name


NONE_TUPLE = (None, None)

TYPE_DIRECTIVE = 1
TYPE_COMMAND = 2
TYPE_OPERATOR = 3
TYPE_ARGUMENT = 4
TYPE_SCALAR = 5
