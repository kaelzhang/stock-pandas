from stock_pandas.directive import Parser
from stock_pandas import DirectiveCache

def test_basic():
    increase = 'increase:(ma:20,close),3'

    FORMS = [
        (increase, increase),
        ("""
        increase :
            (
                ma:
                    20,
                    close
            ),
            3
        """, increase),
        (
            'repeat : (kdj.j < 0), 5',
            'repeat:(kdj.j<0.0),5'
        )
    ]

    for input, expect in FORMS:
        parser = Parser(input, DirectiveCache())
        parsed = parser.parse()

        assert str(parsed) == expect

