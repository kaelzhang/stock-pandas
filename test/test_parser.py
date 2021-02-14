import pytest

from stock_pandas.directive import Parser
from stock_pandas.common import (
    TYPE_DIRECTIVE,
    TYPE_COMMAND,
    TYPE_OPERATOR,
    TYPE_ARGUMENT,
    TYPE_SCALAR
)
from stock_pandas.exceptions import DirectiveSyntaxError


def convert(result):
    if result is None:
        return

    if isinstance(result, list):
        return [convert(x) for x in result]

    label = result.label
    data = result.data

    if label in [
        TYPE_OPERATOR,
        TYPE_SCALAR
    ]:
        return data[0]

    return label, tuple([
        convert(x) for x in data
    ])


def test_basic():
    increase = 'increase:(ma:20,close),3'
    increase_structure = (
        TYPE_DIRECTIVE,
        (
            (
                TYPE_COMMAND, (
                    'increase',
                    None,
                    [
                        (
                            TYPE_ARGUMENT,
                            ((
                                TYPE_DIRECTIVE,
                                (
                                    (
                                        TYPE_COMMAND,
                                        (
                                            'ma',
                                            None,
                                            [
                                                (
                                                    TYPE_ARGUMENT,
                                                    ('20',)
                                                ),
                                                (
                                                    TYPE_ARGUMENT,
                                                    ('close',)
                                                )
                                            ]
                                        )
                                    ),
                                    None,
                                    None
                                )
                            ),)
                        ),
                        (
                            TYPE_ARGUMENT,
                            ('3',)
                        )
                    ]
                )
            ),
            None,
            None
        )
    )

    FORMS = [
        (
            increase,
            increase_structure
        ),
        ("""
        increase :
            (
                ma:
                    20,
                    close
            ),
            3
        """, increase_structure),
        (
            'repeat.haha : (kdj.j < 0), 5',
            (
                TYPE_DIRECTIVE,
                (
                    (
                        TYPE_COMMAND,
                        (
                            'repeat',
                            'haha',
                            [
                                (
                                    TYPE_ARGUMENT,
                                    ((
                                        TYPE_DIRECTIVE,
                                        (
                                            (
                                                TYPE_COMMAND,
                                                (
                                                    'kdj',
                                                    'j',
                                                    []
                                                )
                                            ),
                                            '<',
                                            0.0
                                        )
                                    ),)
                                ),

                                (
                                    TYPE_ARGUMENT,
                                    ('5',)
                                )
                            ]
                        )
                    ),
                    None,
                    None
                )
            )
        ),
        (
            'ma:5 \\ ma:10',
            (
                TYPE_DIRECTIVE,
                (
                    (
                        TYPE_COMMAND,
                        (
                            'ma',
                            None,
                            [
                                (
                                    TYPE_ARGUMENT,
                                    ('5',)
                                )
                            ]
                        )
                    ),
                    '\\',
                    (
                        TYPE_COMMAND,
                        (
                            'ma',
                            None,
                            [
                                (
                                    TYPE_ARGUMENT,
                                    ('10',)
                                )
                            ]
                        )
                    )
                )
            )
        )
    ]

    for input, expect in FORMS:
        parser = Parser(input)
        parsed = parser.parse()

        assert convert(parsed) == expect


def test_invalid_columns():
    CASES = [
        ('a >', 'unexpected EOF'),
        ('>', 'unexpected token'),
        ('ma:>0', 'unexpected token'),
        ('ma >> 1', 'invalid operator'),
        ('ma:(abc', 'unexpected EOF'),
        ('ma > 0 >', 'expect EOF'),
        ('ma:(abc > 0 >', 'unexpected token'),
        ('ma:5 > 0)', 'expect EOF')
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
        (
            column:close >> boll.upper
        ),
        5
''').parse()
    except Exception as e:
        print()
        print(e)
