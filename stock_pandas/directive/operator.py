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
    return cross & ~ less


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
    return left == right


def not_equal(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left != right


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


def logical_or(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left | right


def logical_and(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left & right


OPERATORS = {
    '//': cross_up,
    '\\': cross_down,
    '><': cross,
    '<': less_than,
    '<=': less_than_or_equal,
    '==': equal,
    '!=': not_equal,
    '>=': larger_than_or_equal,
    '>': larger_than,
    '|': logical_or,
    '&': logical_and
}


def plus(
    array: NDArrayAny
) -> NDArrayAny:
    return array


def minus(
    array: NDArrayAny
) -> NDArrayAny:
    return - array


def not_operator(
    array: NDArrayAny
) -> NDArrayAny:
    return ~ array


# + directive
# - directive
# ~ directive
UNERY_OPERATORS = {
    '+': plus,
    '-': minus,
    '~': not_operator
}
