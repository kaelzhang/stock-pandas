import pytest

from stock_pandas.column import (
    parse_column_name
)

def test_valid_columns():
    CASES = [
        (
            # columnn name
            'foo',
            # command name
            'foo',
            # sub command
            None,
            # arguments
            [],
            # operator
            None,
            # expression
            None
        ),
        (
            'foo.bar',
            'foo',
            'bar',
            [],
            None,
            None
        ),
        (
            'foo.bar:1',
            'foo',
            'bar',
            ['1'],
            None,
            None
        ),
        (
            # redundant whitespaces
            ' foo.bar:1,2  >>  0 ',
            'foo',
            'bar',
            ['1', '2'],
            # invalid operator actually
            '>>',
            0
        )
    ]

    for c, cc, sc, a, o, e in CASES:
        command, operator, value = parse_column_name(c)

        assert command.name == cc
        assert command.sub == sc
        assert command.args == a
        assert operator == o
        assert e == value

def test_column_with_two_command():
    c, o, cc = parse_column_name(
        'foo.bar: 1, 2 ,3 / baz.qux :1 ,2,3')

    assert c.name == 'foo'
    assert c.sub == 'bar'
    assert c.args == ['1', '2', '3']
    assert o == '/'
    assert cc.name == 'baz'
    assert cc.sub == 'qux'
    assert cc.args == ['1', '2', '3']

def test_invalid_columns():
    with pytest.raises(ValueError, match='invalid column'):
        parse_column_name('a >')

    with pytest.raises(ValueError, match='invalid column'):
        parse_column_name('>')

    with pytest.raises(ValueError, match='invalid command'):
        parse_column_name('a1')
