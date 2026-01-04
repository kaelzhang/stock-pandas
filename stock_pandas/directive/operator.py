from typing import (
    Union,
    Callable,
    Any,
    TypeVar,
    Dict
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
type OperatorMap[OF] = Dict[str, OF]


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
    '||': logical_or,
    '&&': logical_and
}


def bitwise_or(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left | right


BITWISE_OR_OPERATORS: OperatorMap[OperatorFormula] = {
    '|': bitwise_or,
}


def bitwise_xor(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left ^ right


BITWISE_XOR_OPERATORS: OperatorMap[OperatorFormula] = {
    '^': bitwise_xor,
}


def bitwise_and(
    left: NDArrayAny,
    right: NDArrayAny
) -> NDArrayAny:
    return left & right


BITWISE_AND_OPERATORS: OperatorMap[OperatorFormula] = {
    '&': bitwise_and,
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
    '<': less_than,
    '<=': less_than_or_equal,
    '>=': larger_than_or_equal,
    '>': larger_than,
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
    '==': equal,
    '!=': not_equal,
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
    '//': cross_up,
    '\\': cross_down,
    '><': cross
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
    '+': addition,
    '-': subtraction
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
    '*': multiplication,
    '/': division
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
    '-': minus,
    '~': not_operator
}
