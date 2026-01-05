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
type OperatorMap[OF] = Dict[
    str,
    Tuple[
        # Formula
        OF,
        # Priority, the smaller the higher
        int
    ]
]


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


LOGICAL_OPERATORS: OperatorMap[OperatorFormula] = {
    '||': (logical_or, 9),
    '&&': (logical_and, 9)
}


def bitwise_or(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left | right


BITWISE_OR_OPERATORS: OperatorMap[OperatorFormula] = {
    '|': (bitwise_or, 8)
}


def bitwise_xor(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left ^ right


BITWISE_XOR_OPERATORS: OperatorMap[OperatorFormula] = {
    '^': (bitwise_xor, 7),
}


def bitwise_and(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left & right


BITWISE_AND_OPERATORS: OperatorMap[OperatorFormula] = {
    '&': (bitwise_and, 6),
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
    '<': (less_than, 5),
    '<=': (less_than_or_equal, 5),
    '>=': (larger_than_or_equal, 5),
    '>': (larger_than, 5),
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
    '==': (equal, 4),
    '!=': (not_equal, 4),
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
    '//': (cross_up, 3),
    '\\': (cross_down, 3),
    '><': (cross, 3)
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
    '+': (addition, 2),
    '-': (subtraction, 2)
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
    '*': (multiplication, 1),
    '/': (division, 1)
}


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
UNARY_OPERATORS: OperatorMap[UnaryOperatorFormula] = {
    '-': (minus, 0),
    '~': (not_operator, 0)
}
