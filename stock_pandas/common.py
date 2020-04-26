from functools import partial
from typing import (
    Callable,
    Optional,
    Tuple,
    TypeVar,
    Type
)

import numpy as np
from pandas import DataFrame

T = TypeVar('T', int, float)


def to_number(
    type_ctr: Type[T],
    type_name: str,
    name: str,
    larger_than: T,
    raw_value: str
) -> T:
    try:
        value = type_ctr(raw_value)
    except ValueError:
        raise ValueError(
            f'{name} must be a positive {type_name}, but got `{raw_value}`'
        )

    if value <= larger_than:
        raise ValueError(f'{name} must be greater than {larger_than}')

    return value


period_to_int = partial(to_number, int, 'int', 'period', 1)
repeat_to_int = partial(to_number, int, 'int', 'repeat', 0)

times_to_float = partial(to_number, float, 'float', 'times', 0.)


def create_enum(choices: list, name: str, value: str) -> str:
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


KEY_ALIAS_MAP = '__stock_aliases_map'
KEY_COLUMNS_INFO_MAP = '__stock_columns_info_map'
KEY_DIRECTIVES_CACHE = '__stock_directives_cache'


def copy_stock_metas(source, target) -> None:
    columns = target.columns

    # If the new dataframe has been truncated,
    # Then we need to clean the column info

    # We just set the size of the info to zero to avoid complexity
    need_clean = len(target) < len(source)

    source_aliases_map = getattr(source, KEY_ALIAS_MAP, None)

    if source_aliases_map is not None:
        aliases_map = {}
        for alias, column in source_aliases_map.items():
            # Column `column` might be dropped in `target`
            # by dataframe.drop(columns=some_columns)
            # so we need to check it

            # TODO: if alias is in columns, something wrong happened
            # - support .iloc, loc, and other indexing and setting methods
            if column in columns:
                aliases_map[alias] = column

        # Use `object.__setattr__` to avoid pandas UserWarning:
        # > Pandas doesn't allow columns to be created via a new attribute name
        object.__setattr__(target, KEY_ALIAS_MAP, aliases_map)

    source_columns_info_map = getattr(source, KEY_COLUMNS_INFO_MAP, None)

    if source_columns_info_map is not None:
        columns_info_map = {}
        for column, info in source_columns_info_map.items():
            if column in columns:

                # Set the size to 0,
                # which indicates that the column needs to be calculated again
                columns_info_map[
                    column
                ] = info.update(0) if need_clean else info

        object.__setattr__(target, KEY_COLUMNS_INFO_MAP, columns_info_map)

    source_stock_directives_cache = getattr(source, KEY_DIRECTIVES_CACHE, None)

    if source_stock_directives_cache is not None:
        object.__setattr__(
            target,
            KEY_DIRECTIVES_CACHE,
            source_stock_directives_cache
        )


def ensure_return_type(
    cls,
    method: str,
    should_apply_constructor: bool
) -> None:
    def helper(self, *args, **kwargs):
        ret = getattr(super(cls, self), method)(*args, **kwargs)

        if should_apply_constructor:
            ret = cls(ret)

        copy_stock_metas(self, ret)

        return ret

    helper.__doc__ = getattr(DataFrame, method).__doc__

    setattr(cls, method, helper)


def create_meta_property(key, create, self):
    value = getattr(self, key, None)

    if value is not None:
        return value

    value = create()
    object.__setattr__(self, key, value)
    return value


def meta_property(key, create):
    return property(partial(create_meta_property, key, create))


def compare_cross(
    left: np.ndarray,
    right: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    less = right < left

    # matrix or vector of all False value
    cross = np.zeros_like(less)

    if len(cross) > 1:
        # Find cross
        cross[1:] = np.diff(less)

    return cross, less


ARGS_SEPARATOR = ','


def join_args(args: list) -> str:
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
    """Creates a `period`-period rolling window and apply
    `func` to the items
    """

    length = len(array)

    if period > length:
        return np.repeat(fill, length)

    unshifted = np.apply_along_axis(
        func,
        1,
        rolling_window(array, period, stride)
    )

    return shift_and_fill(unshifted, period, fill)


DEFAULT_ARG_VALUE = ''


def command_full_name(
    name: str,
    sub: Optional[str]
) -> str:
    return name if sub is None else f'{name}.{sub}'


NONE_TUPLE = (None, None)

TYPE_DIRECTIVE = 1
TYPE_COMMAND = 2
TYPE_OPERATOR = 3
TYPE_ARGUMENT = 4
TYPE_SCALAR = 5
