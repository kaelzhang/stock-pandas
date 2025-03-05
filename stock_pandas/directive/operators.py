from stock_pandas.common import (
    compare_cross,
    NDArrayAny
)


def cross(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    cross, _ = compare_cross(left, right)
    return cross


def cross_up(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    cross, less = compare_cross(left, right)
    return cross & less  # type: ignore


def cross_down(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    cross, less = compare_cross(left, right)
    return cross & ~ less  # type: ignore


def less_than(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left < right


def less_than_or_equal(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left <= right


def equal(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left == right  # type: ignore


def larger_than_or_equal(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left >= right


def larger_than(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left > right


OPERATORS = {
    '><': cross,
    '/': cross_up,
    '\\': cross_down,
    '<': less_than,
    '<=': less_than_or_equal,
    '==': equal,
    '>=': larger_than_or_equal,
    '>': larger_than
}
