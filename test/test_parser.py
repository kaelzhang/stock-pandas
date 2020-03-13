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
        ('a >', 'unexpected EOF', DirectiveSyntaxError),
        ('>', 'unexpected token', DirectiveSyntaxError),
        # ('a1', 'unknown command', DirectiveValueError),
        # ('foo', 'unknown command', DirectiveValueError),
        ('ma >> 1', 'invalid operator', DirectiveSyntaxError),
        ('ma:(abc', 'unexpected EOF', DirectiveSyntaxError),
        # ('kdj', 'sub command should be specified', DirectiveValueError),
        # ('ma > foo', 'unknown command', DirectiveValueError)
    ]

    parse = lambda input: Parser(input).parse()

    for directive_str, err_msg, err in CASES:
        with pytest.raises(err, match=err_msg):
            parse(directive_str)

    # with pytest.raises(DirectiveValueError, match='accepts max'):
    #     parse('ma:2,close,3')

    # with pytest.raises(ValueError, match='is required'):
    #     parse('ma')

    # with pytest.raises(ValueError, match='no sub'):
    #     parse('ma.nosub')

    # with pytest.raises(ValueError, match='unknown sub'):
    #     parse('macd.unknown')
