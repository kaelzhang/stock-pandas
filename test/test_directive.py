import pytest

from stock_pandas.directive import Parser
from stock_pandas import *

def parse(string):
    return Parser(string, DirectiveCache()).parse()

def run_case(case, apply=False):
    c, cc, sc, a, o, e, s = case
    print('directive:', c)

    directive = parse(c)

    command = directive.command
    operator = directive.operator
    value = directive.expression

    assert command.name == cc
    assert command.sub == sc
    assert command.args == a

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
            [26, 12],
            # operator
            None,
            # expression
            None,
            # to string
            'macd:26,12'
        ),
        (
            'macd.signal',
            'macd',
            'signal',
            [26, 12, 9],
            None,
            None,
            'macd.signal:26,12,9'
        )
    ]

    print()

    for case in CASES:
        run_case(case, True)

def test_column_with_two_command_real_case():
    directive = parse('ma:10 > boll.upper:20')
    directive.apply_presets()

    expr = directive.expression

    assert expr.name == 'boll'
    assert expr.sub == 'upper'
    assert expr.args == [20, 2, 'close']


def test_invalid_columns():
    CASES = [
        ('a >', 'unknown command', DirectiveValueError),
        ('>', 'unexpected token', DirectiveSyntaxError),
        ('a1', 'unknown command', DirectiveValueError),
        ('foo', 'unknown command', DirectiveValueError),
        ('ma >> 1', 'invalid operator', DirectiveSyntaxError),
        ('ma:(abc', 'unbalanced', DirectiveSyntaxError),
        ('kdj', 'sub command should be specified', DirectiveValueError),
        ('ma > foo', 'unknown command', DirectiveValueError)
    ]

    for directive_str, err_msg, err in CASES:
        with pytest.raises(err, match=err_msg):
            parse(directive_str)

    with pytest.raises(ValueError, match='accepts max'):
        parse('ma:1,close,3')

    with pytest.raises(ValueError, match='is required'):
        parse('ma')

    with pytest.raises(ValueError, match='no sub'):
        parse('ma.nosub')

    with pytest.raises(ValueError, match='unknown sub'):
        parse('macd.unknown')
