import pytest

from stock_pandas.directive import parse as parse_it
from stock_pandas import (
    DirectiveValueError,
    DirectiveCache
)


def parse(string):
    return parse_it(string, DirectiveCache())


def run_case(case, apply=False):
    c, cc, sc, a, o, e, s = case
    print('directive:', c)

    directive = parse(c)

    command = directive.command
    operator = directive.operator
    value = directive.expression

    assert command.name == cc
    assert command.sub == sc
    assert [a.value for a in command.args] == a

    if o is None:
        assert operator == o
    else:
        assert operator.name == o

    assert e == value
    assert s == str(directive)


def test_valid_columns_after_apply():
    CASES = [
        (
            # directive
            'macd.dif',
            # command name
            'macd',
            # sub command
            None,
            # arguments
            [12, 26],
            # operator
            None,
            # expression
            None,
            # to string
            'macd:12,26'
        ),
        (
            'macd.signal',
            'macd',
            'signal',
            [12, 26, 9],
            None,
            None,
            'macd.signal:12,26,9'
        )
    ]

    print()

    for case in CASES:
        run_case(case, True)


def test_column_with_two_command_real_case():
    directive = parse('ma:10 > boll.upper:20')

    expr = directive.expression

    assert expr.name == 'boll'
    assert expr.sub == 'upper'
    assert [a.value for a in expr.args] == [20, 2, 'close']


def test_value_error():
    CASES = [
        ('a1', 'unknown command'),
        ('foo', 'unknown command'),
        ('kdj', 'sub command should be specified'),
        ('ma:2 > foo', 'unknown command'),
        ('ma:2,close,3', 'accepts max'),
        ('ma:1', 'greater than 1'),
        ('ma:close', 'positive int'),
        ('ma', 'is required'),
        ('ma.nosub', 'no sub'),
        ('macd.unknown', 'unknown sub'),
        ('style:cartoon', 'should be either'),
        ('increase:close,5,3', 'direction'),
        ('kdj.j:9,3,3,a', 'a float'),
        ('kdj.j:9,3,3,200', 'in between')
    ]

    for directive_str, err_msg in CASES:
        with pytest.raises(DirectiveValueError, match=err_msg):
            parse(directive_str)
