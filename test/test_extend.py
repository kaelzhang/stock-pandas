import pytest

from stock_pandas import (
    StockDataFrame,
    CommandDefinition
)
from stock_pandas.commands.base import BUILTIN_COMMANDS

from .common import (
    get_tencent
)


sub_commands = BUILTIN_COMMANDS['kdj'].sub_commands.copy()

StockDataFrame.define_command('kdj2', CommandDefinition(
    sub_commands=sub_commands
))


@pytest.fixture
def stock():
    return get_tencent()

def test_kdj(stock):
    assert stock['kdj2.j']['2020-02-07'] > 120
    assert stock['kdj2.j']['2020-01-31'] < -1
    assert stock['kdj2.j']['2020-02-24'] < -14

    kdjj = stock['kdj2.j']['2020-02-07']
    assert stock['kdj2.j:9,3,3,50']['2020-02-07'] == kdjj
