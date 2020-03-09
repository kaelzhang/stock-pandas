import pytest

from stock_pandas.directive import Directive

def test_valid_columns():
    CASES = [
        (
            # columnn name
            'sma',
            # command name
            'sma',
            # sub command
            None,
            # arguments
            [],
            # operator
            None,
            # expression
            None,
            # to string
            'sma'
        ),
        (
            'sma.bar',
            'sma',
            'bar',
            [],
            None,
            None,
            'sma.bar'
        ),
        (
            'sma.bar:1',
            'sma',
            'bar',
            ['1'],
            None,
            None,
            'sma.bar:1'
        ),
        (
            # redundant whitespaces
            ' sma.bar:1,2  >  0 ',
            'sma',
            'bar',
            ['1', '2'],
            # invalid operator actually
            '>',
            0,

            # 0 will convert to float
            'sma.bar:1,2>0.0'
        )
    ]

    print()

    for c, cc, sc, a, o, e, s in CASES:
        print('directive:', c)

        directive = Directive.from_string(c, True)
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

def test_column_with_two_command():
    column = Directive.from_string('sma.bar: 1, 2 ,3 / boll.qux :1 ,2,3', True)
    c = column.command
    o = column.operator
    cc = column.expression

    assert c.name == 'sma'
    assert c.sub == 'bar'
    assert c.args == ['1', '2', '3']
    assert o.name == '/'
    assert cc.name == 'boll'
    assert cc.sub == 'qux'
    assert cc.args == ['1', '2', '3']
    assert str(column) == 'sma.bar:1,2,3/boll.qux:1,2,3'

def test_invalid_columns():
    with pytest.raises(ValueError, match='invalid directive'):
        Directive.from_string('a >', True)

    with pytest.raises(ValueError, match='invalid directive'):
        Directive.from_string('>', True)

    with pytest.raises(ValueError, match='invalid command'):
        Directive.from_string('a1', True)

    with pytest.raises(ValueError, match='unknown command'):
        Directive.from_string('foo', True)

    with pytest.raises(ValueError, match='invalid operator'):
        Directive.from_string('sma >> 1', True)
