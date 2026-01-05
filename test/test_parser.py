import pytest

from stock_pandas import (
    CommandDefinition,
    CommandPreset,
    CommandArg
)

from stock_pandas.directive.parser import Parser
from stock_pandas.exceptions import DirectiveSyntaxError

from .common import (
    parse,
    COMMANDS
)


def test_invalid_columns():
    CASES = [
        ('a >', 'unexpected EOF'),
        ('>', 'unexpected token'),
        ('ma@(abc', 'unexpected EOF'),
        ('ma > 0 >', 'unexpected EOF'),
        ('ma@(abc > 0 >', 'unexpected EOF'),
        ('ma:5 > 0)', 'expect EOF'),
        ('boll > ~1', 'unexpected token "1"')
    ]

    def parse(input):
        return Parser(input).parse()

    for directive_str, err_msg in CASES:
        with pytest.raises(DirectiveSyntaxError, match=err_msg):
            parse(directive_str)


def test_invalid_directive():
    try:
        Parser('''
repeat
    :
        5

    @   (
            column@close >> boll.upper
        )
''').parse()
    except Exception as e:
        assert e.line == 7, 'line'
        assert e.column == 26, 'column'
        print()
        print(e)


def test_stringify():
    cases = [
        ('close + open * high', 'close+open*high', 'operator priority'),
        ('boll:20@close', 'boll', 'command default value'),
        ('close + - close', 'close+-close', 'unary operator'),
        ('boll:-close', 'boll-close', 'unclosed command'),
        ('boll > -1', 'boll>-1', 'negative number'),
        ('3 * (high - low)', '3*(high-low)', 'wrapped directive'),
        ('boll:30,', 'boll:30', 'command args end fast, but it is ok'),
        ('kdj.j:,4', 'kdj.j:,4', 'default argument'),
        ('kdj.j:@,high', 'kdj.j@,high', 'default series argument'),
        ('~ ( kdj.j < 0 )', '~(kdj.j<0)', 'unary expression'),
        (
            '(kdj.j > 100) | (kdj.j <= 100)',
            'kdj.j>100|kdj.j<=100',
            'logical operator'
        ),
        (
            'kdj.j > 100 | kdj.j <= 100',
            'kdj.j>100|kdj.j<=100',
            'logical operator'
        ),
        ('(kdj.j)&(kdj.d)', 'kdj.j&kdj.d', 'unnecessary ()')
    ]

    for i, (input, stringified, desc) in enumerate(cases):
        parsed = parse(input)
        assert str(parsed) == stringified, f'{i}: {desc}'


def test_edge_command_cases():
    COMMANDS['nonexists'] = CommandDefinition(
        CommandPreset(
            formula=lambda: None,
            lookback=lambda *_: 0,
            args=[],
            series=[]
        )
    )

    parsed = parse('nonexists:')
    assert str(parsed) == 'nonexists', 'nonexists'

    COMMANDS['nonexists2'] = CommandDefinition(
        CommandPreset(
            formula=lambda: None,
            lookback=lambda *_: 0,
            args=[CommandArg(default=None)],
            series=[]
        )
    )

    parsed = parse('nonexists2:high')
    assert str(parsed) == 'nonexists2:high', 'nonexists2'


# def test_aaa():
#     parsed = parse('(kdj.j) & (kdj.d)')
#     print(parsed)
