from functools import partial

import pytest

from stock_pandas import (
    COMMANDS,
    CommandPreset
)
from stock_pandas.commands.over_bought_or_sold import kdj_j

from .common import (
    get_tencent
)


kdj = COMMANDS['kdj'][1].copy()

COMMANDS['kdj2'] = (
    None,
    kdj,
    None
)

kdj['j'] = CommandPreset(
    partial(kdj_j, 'kdj2'),
    [9, 3, 3, 50.]
)


@pytest.fixture
def stock():
    return get_tencent()

def test_kdj(stock):
    assert stock['kdj2.j']['2020-02-07'] > 120
    assert stock['kdj2.j']['2020-01-31'] < -1
    assert stock['kdj2.j']['2020-02-24'] < -14

    kdjj = stock['kdj2.j']['2020-02-07']
    assert stock['kdj2.j:9,3,3,50']['2020-02-07'] == kdjj
