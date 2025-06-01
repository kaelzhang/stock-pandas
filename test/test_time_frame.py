import pytest
import numpy as np

from typing import Union

from stock_pandas import (
    StockDataFrame,
    TimeFrame,
    cumulators
)

from .common import (
    get_1m_tencent,
    TIME_KEY
)


def test_time_frame_str():
    assert str(TimeFrame.m1) == '1m'
    assert str(TimeFrame.D1) == '1d'
    assert str(TimeFrame.M1) == '1M'
    assert f'{TimeFrame.m5}' == '5m'


def test_time_frame_error():
    with pytest.raises(ValueError, match='invalid'):
        StockDataFrame(time_frame='1')


def _test_redefine_time_frame(time_frame: Union[str, TimeFrame]):
    stock = StockDataFrame(
        get_1m_tencent().iloc[:20],
        date_col=TIME_KEY,
        time_frame=time_frame
    )

    new_stock = StockDataFrame(
        stock,
        cumulators={
            'open': cumulators['open']
        }
    )

    stock = stock.cumulate()
    new_stock = new_stock.cumulate()

    assert np.array_equal(
        stock['open'].to_numpy(),
        new_stock['open'].to_numpy()
    )

    assert np.array_equal(
        stock['close'].to_numpy(),
        new_stock['close'].to_numpy()
    )

def test_redefine_time_frame():
    _test_redefine_time_frame('5m')
    _test_redefine_time_frame(TimeFrame.m5)
