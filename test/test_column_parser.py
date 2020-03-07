import pytest

from stock_pandas.parser import ColumnName

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
            None,
            # to string
            'foo'
        ),
        (
            'foo.bar',
            'foo',
            'bar',
            [],
            None,
            None,
            'foo.bar'
        ),
        (
            'foo.bar:1',
            'foo',
            'bar',
            ['1'],
            None,
            None,
            'foo.bar:1'
        ),
        (
            # redundant whitespaces
            ' foo.bar:1,2  >  0 ',
            'foo',
            'bar',
            ['1', '2'],
            # invalid operator actually
            '>',
            0,

            # 0 will convert to float
            'foo.bar:1,2>0.0'
        )
    ]

    for c, cc, sc, a, o, e, s in CASES:
        column = ColumnName.from_string(c)

        command = column.command
        operator = column.operator
        value = column.expression

        assert command.name == cc
        assert command.sub == sc
        assert command.args == a
        assert operator == o
        assert e == value
        assert s == str(column)

def test_column_with_two_command():
    column = ColumnName.from_string('foo.bar: 1, 2 ,3 / baz.qux :1 ,2,3')
    c = column.command
    o = column.operator
    cc = column.expression

    assert c.name == 'foo'
    assert c.sub == 'bar'
    assert c.args == ['1', '2', '3']
    assert o == '/'
    assert cc.name == 'baz'
    assert cc.sub == 'qux'
    assert cc.args == ['1', '2', '3']
    assert str(column) == 'foo.bar:1,2,3/baz.qux:1,2,3'

def test_invalid_columns():
    with pytest.raises(ValueError, match='invalid column'):
        ColumnName.from_string('a >')

    with pytest.raises(ValueError, match='invalid column'):
        ColumnName.from_string('>')

    with pytest.raises(ValueError, match='invalid command'):
        ColumnName.from_string('a1')

    with pytest.raises(ValueError, match='invalid operator'):
        ColumnName.from_string('a1 >> 1')
