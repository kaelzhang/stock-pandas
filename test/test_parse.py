import warnings

from stock_pandas import (
    DirectiveValueError,
    DirectiveNonSenseWarning
)

from .common import parse


def test_column_with_two_command_real_case():
    directive = parse('ma:10 > boll.upper:20')

    expr = directive.right

    assert expr.name == 'boll.upper'
    assert expr.args == [20, 2]
    assert expr.series == ['close']


def test_value_error():
    CASES = [
        ('kdj', 'sub command should be specified'),
        ('ma:2,3@close', 'accepts max'),
        ('ma:1', 'greater than 1'),
        ('ma:close', 'positive int'),
        ('ma', 'is required'),
        ('ma.nosub', 'no sub'),
        ('macd.unknown', 'unknown sub'),
        ('style:cartoon', 'should be either'),
        ('increase:5,3@close', 'direction'),
        ('kdj.j:9,3,3,a', 'a float'),
        ('kdj.j:9,3,3,200', 'in between'),
        ('hv:10,invalid', '`invalid` is not a valid time frame'),
        ('hv:10,15m,invalid', '`invalid` is not a valid trading days'),
        ('hv:10,15m,0', 'but got `0`'),
        ('hv:10,15m,366', 'but got `366`'),
        ('kdj.j:9,3,3,invalid', 'must be a float'),
        ('kdj.j:9,3,3,1000', 'between 0 and 100'),
        ('invalid:a', 'unknown command'),
        ('ma:2@foo,bar', 'accepts max 1'),
        ('change:2', 'series[0] is required for command "change"')
    ]

    for i, (directive_str, err_msg) in enumerate(CASES):
        err_msgs = err_msg if isinstance(err_msg, list) else [err_msg]

        for err_msg in err_msgs:
            try:
                parse(directive_str)
            except Exception as e:
                assert err_msg in str(e)
                assert isinstance(e, DirectiveValueError)
                continue

            raise Exception(
                f'{i}: `{directive_str}` should raise error: {err_msg}'
            )


def test_directive_warning():
    warnings.simplefilter('error', DirectiveNonSenseWarning)

    CASES = [
        ('1 > 2', 1, 1),
        ('''(
    close > boll.upper
) & (
    0 > -1
)''', 4, 5)
    ]

    for i, (directive_str, line, column) in enumerate(CASES):
        try:
            parse(directive_str)
        except DirectiveNonSenseWarning as e:
            assert 'it is a non-sense directive without any command' in str(e)
            assert e.line == line
            assert e.column == column
        else:
            raise Exception(f'{i}: `{directive_str}` should raise DirectiveNonSenseWarning')

