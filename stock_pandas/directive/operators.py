from numpy import ndarray
from stock_pandas.common import compare_cross


def cross(
    left: ndarray,
    right: ndarray
) -> ndarray:
    cross, _ = compare_cross(left, right)
    return cross


def cross_up(
    left: ndarray,
    right: ndarray
) -> ndarray:
    cross, less = compare_cross(left, right)
    return cross & less


def cross_down(
    left: ndarray,
    right: ndarray
) -> ndarray:
    cross, less = compare_cross(left, right)
    return cross & ~ less


def less_than(
    left: ndarray,
    right: ndarray
) -> ndarray:
    return left < right


def less_than_or_equal(
    left: ndarray,
    right: ndarray
) -> ndarray:
    return left <= right


def equal(
    left: ndarray,
    right: ndarray
) -> ndarray:
    return left == right


def larger_than_or_equal(
    left: ndarray,
    right: ndarray
) -> ndarray:
    return left >= right


def larger_than(
    left: ndarray,
    right: ndarray
) -> ndarray:
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
