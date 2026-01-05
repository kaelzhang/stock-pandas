from stock_pandas.directive.parse import (
    parse as parse_it,
    # DirectiveCache
)
from stock_pandas.commands.base import BUILTIN_COMMANDS
from stock_pandas import (
    DirectiveValueError,
    DirectiveCache
)


COMMANDS = BUILTIN_COMMANDS.copy()

def parse(string):
    return parse_it(string, DirectiveCache(), COMMANDS)


def test_column_with_two_command_real_case():
    directive = parse('ma:10 > boll.upper:20')

    expr = directive.right

    assert expr.name == 'boll.upper'
    assert expr.args == [20, 2]
    assert expr.series == ['close']


def test_value_error():
    CASES = [
        ('kdj', 'sub command should be specified'),
        ('ma:2,close,3', 'accepts max'),
        ('ma:1', 'greater than 1'),
        ('ma:close', 'positive int'),
        ('ma', 'is required'),
        ('ma.nosub', 'no sub'),
        ('macd.unknown', 'unknown sub'),
        ('style:cartoon', 'should be either'),
        ('increase:close,5,3', 'direction'),
        ('kdj.j:9,3,3,a', 'a float'),
        ('kdj.j:9,3,3,200', 'in between'),
        ('hv:10,invalid', '`invalid` is not a valid time frame'),
        ('hv:10,15m,invalid', '`invalid` is not a valid trading days'),
        ('hv:10,15m,0', 'but got `0`'),
        ('hv:10,15m,366', 'but got `366`'),
    ]

    for i, (directive_str, err_msg) in enumerate(CASES):
        err_msgs = err_msg if isinstance(err_msg, list) else [err_msg]

        for err_msg in err_msgs:
            try:
                parse(directive_str)
            except Exception as e:
                assert err_msg in str(e)
                assert isinstance(e, DirectiveValueError)
                return

            raise Exception(f'{i}: {directive_str} -> {err_msg}')
