from .common import compare_cross


def cross(left, right):
    cross, _ = compare_cross(left, right)
    return cross


def cross_up(left, right):
    cross, less = compare_cross(left, right)
    return cross & less


def cross_down(left, right):
    cross, less = compare_cross(left, right)
    return cross & ~ less


def less_than(left, right):
    return left < right


def less_than_or_equal(left, right):
    return left <= right


def equal(left, right):
    return left == right


def larger_than_or_equal(left, right):
    return left >= right


def larger_than(left, right):
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
