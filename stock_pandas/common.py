from functools import partial
from typing import (
    Callable,
    Optional,
    Tuple,
    TypeVar,
    Type
)

import numpy as np


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
    # A byte stride for float is 8
    byte_stride: int = 8
) -> np.ndarray:
    """Gets an `period`-period rolling window for 1d array
    """

    return np.lib.stride_tricks.as_strided(
        array,
        shape=(len(array) - period + 1, period),
        strides=(byte_stride, byte_stride)
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
    # Not the stride of window, but the byte stride of np.ndarray.
    # The stride of window is always `1` for stock-pandas?
    byte_stride: int = 8,
    shift: bool = True
) -> np.ndarray:
    """Creates a `period`-period rolling window and apply
    `func` to the items

    Args:
        shift (:obj:`bool`, optional)
    """

    length = len(array)

    if period > length:
        return np.repeat(fill, length)

    unshifted = np.apply_along_axis(
        func,
        1,
        rolling_window(array, period, byte_stride)
    )

    if shift:
        # If use shift, then we will add values to the begin of the array
        return shift_and_fill(unshifted, period, fill)

    # If no shift
    return np.append(unshifted, np.repeat(fill, period - 1))


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
