from stock_pandas.directive import Parser
from stock_pandas.directive.factory import (
    TYPE_DIRECTIVE,
    TYPE_COMMAND,
    TYPE_OPERATOR,
    TYPE_FLOAT,
    TYPE_TEXT
)

def convert(result):
    if result is None:
        return

    if isinstance(result, list):
        return [convert(x) for x in result]

    label = result.label
    data = result.data

    if label in [
        TYPE_OPERATOR,
        TYPE_FLOAT,
        TYPE_TEXT
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
                            TYPE_DIRECTIVE,
                            (
                                (
                                    TYPE_COMMAND,
                                    (
                                        'ma',
                                        None,
                                        [
                                            '20',
                                            'close'
                                        ]
                                    )
                                ),
                                None,
                                None
                            )
                        ),
                        '3'
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
                                ),

                                '5'
                            ]
                        )
                    ),
                    None,
                    None
                )
            )
        )
    ]

    for input, expect in FORMS:
        parser = Parser(input)
        parsed = parser.parse()
        print(convert(parsed))

        assert convert(parsed) == expect

