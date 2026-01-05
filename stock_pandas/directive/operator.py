from __future__ import annotations

from typing import (
    Union,
    Callable,
    Any,
    TypeVar,
    Dict,
    Tuple
)

from stock_pandas.common import (
    compare_cross,
    NDArrayAny
)

from numpy.typing import NDArray


ReturnType = NDArray[Any]
NumberType = Union[int, float]
OperatorArgType = Union[NumberType, ReturnType]

OperatorFormula = Callable[[OperatorArgType, OperatorArgType], ReturnType]
UnaryOperatorFormula = Callable[[ReturnType], ReturnType]

OF = TypeVar('OF', OperatorFormula, UnaryOperatorFormula)

# Python 3.10 compatible generic type alias
# Using Generic instead of 'type' keyword (which requires Python 3.12+)
OperatorMap = Dict[
    str,
    Tuple[
        # Formula
        OF,
        # Priority, larger the higher
        int
    ]
]


def bitwise_or(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left | right


BITWISE_OR_OPERATORS: OperatorMap[OperatorFormula] = {
    '|': (bitwise_or, 1)
}


def bitwise_xor(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left ^ right


BITWISE_XOR_OPERATORS: OperatorMap[OperatorFormula] = {
    '^': (bitwise_xor, 2),
}


def bitwise_and(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left & right


BITWISE_AND_OPERATORS: OperatorMap[OperatorFormula] = {
    '&': (bitwise_and, 3),
}


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


RELATIONAL_OPERATORS: OperatorMap[OperatorFormula] = {
    '<': (less_than, 4),
    '<=': (less_than_or_equal, 4),
    '>=': (larger_than_or_equal, 4),
    '>': (larger_than, 4),
}


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


EQUALITY_OPERATORS: OperatorMap[OperatorFormula] = {
    '==': (equal, 5),
    '!=': (not_equal, 5),
}


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


STYLE_OPERATORS: OperatorMap[OperatorFormula] = {
    '//': (cross_up, 6),
    '\\': (cross_down, 6),
    '><': (cross, 6)
}


def addition(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left + right


def subtraction(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left - right


ADDITION_OPERATORS: OperatorMap[OperatorFormula] = {
    '+': (addition, 7),
    '-': (subtraction, 7)
}


def multiplication(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left * right


def division(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left / right


MULTIPLICATION_OPERATORS: OperatorMap[OperatorFormula] = {
    '*': (multiplication, 8),
    '/': (division, 8)
}


def minus(
    array: NDArrayAny
) -> NDArrayAny:
    return - array


def not_operator(
    array: NDArrayAny
) -> NDArrayAny:
    return ~ array.astype(bool)


# + directive
# - directive
# ~ directive
UNARY_OPERATORS: OperatorMap[UnaryOperatorFormula] = {
    '-': (minus, 9),
    '~': (not_operator, 9)
}
