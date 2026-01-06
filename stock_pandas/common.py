"""Common utilities for stock-pandas.

This module provides shared utilities and functions used across the package.
"""

from functools import partial
from typing import (
    Callable,
    Optional,
    Tuple,
    TypeVar,
    Type,
    Any,
    List
)

from numpy.typing import (
    NDArray
)

import numpy as np

NDArrayAny = NDArray[Any]


def set_attr(target: Any, key: str, value: Any) -> None:
    object.__setattr__(target, key, value)


T = TypeVar('T', int, float)
ReturnInt = Callable[..., int]
ReturnFloat = Callable[..., float]
ReturnStr = Callable[..., str]


def to_number(
    type_ctr: Type[T],
    type_name: str,
    name: str,
    larger_than: T,
    raw_value: str
) -> T:
    try:
        value = type_ctr(raw_value)
    except ValueError as e:
        raise ValueError(
            f'{name} must be a positive {type_name}, but got `{raw_value}`'
        ) from e

    if value <= larger_than:
        raise ValueError(f'{name} must be greater than {larger_than}')

    return value


period_to_int: ReturnInt = partial(to_number, int, 'int', 'period', 1)
repeat_to_int: ReturnInt = partial(to_number, int, 'int', 'repeat', 0)

times_to_float: ReturnFloat = partial(to_number, float, 'float', 'times', 0.)


def create_enum(choices: List[str], name: str, value: str) -> str:
    if value in choices:
        return value

    choices_str = ' or '.join([f'"{choice}"' for choice in choices])

    raise ValueError(
        f'{name} should be either {choices_str}, but got `{value}`'
    )


style_enums: ReturnStr = partial(create_enum, [
    'bullish',
    'bearish'
], 'style')


def to_direction(value: int) -> int:
    if value == 1 or value == -1:
        return value

    raise ValueError(f'direction must be `1` or `-1`, but got `{value}`')


def compare_cross(
    left: NDArrayAny,
    right: NDArrayAny
) -> Tuple[NDArrayAny, NDArrayAny]:
    less = right < left

    # matrix or vector of all False value
    cross = np.zeros_like(less)

    if len(cross) > 1:
        # Find cross
        cross[1:] = np.diff(less)

    return cross, less


ARGS_SEPARATOR = ','
EMPTY = ''


def join_args(args: List[Optional[Any]]) -> str:
    return ARGS_SEPARATOR.join([
        str(arg) if arg is not None else EMPTY
        for arg in args
    ])


def rolling_window(
    array: NDArrayAny,
    period: int,
    # A byte stride for float is 8
    byte_stride: int = 8
) -> NDArrayAny:
    """Gets an `period`-period rolling window for 1d array
    """

    return np.lib.stride_tricks.as_strided(
        array,
        shape=(len(array) - period + 1, period),
        strides=(byte_stride, byte_stride)
    )


def shift_and_fill(
    array: NDArrayAny,
    period: int,
    fill=np.nan
) -> NDArrayAny:
    """Adds items to the left of an array to meet the min periods
    """

    return np.append(np.repeat(fill, period - 1), array)


def rolling_calc(
    array: NDArrayAny,
    period: int,
    func: Callable,
    fill=np.nan,
    # Not the stride of window, but the byte stride of np.ndarray.
    # The stride of window is always `1` for stock-pandas?
    byte_stride: int = 8,
    shift: bool = True
) -> NDArrayAny:
    """Creates a `period`-period rolling window and apply
    `func` to the items

    Args:
        shift (:obj:`bool`, optional)
    """
    # Note: For min/max operations (llv/hhv), the Rust implementation is
    # called directly in the respective command functions, not through here.

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


def command_full_name(
    name: str,
    sub: Optional[str]
) -> str:
    return name if sub is None else f'{name}.{sub}'
