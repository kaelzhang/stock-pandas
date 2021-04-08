import pytest
import numpy as np

from stock_pandas import (
    StockDataFrame,
    TimeFrame,
    cumulators
)

from .common import (
    get_1m_tencent,
    TIME_KEY
)


def test_time_frame_error():
    with pytest.raises(ValueError, match='invalid'):
        StockDataFrame(time_frame='1')

    with pytest.raises(NotImplementedError):
        StockDataFrame(
            get_1m_tencent(),
            date_col=TIME_KEY,
            time_frame=TimeFrame()
        ).cumulate()


def test_redefine_time_frame():
    stock = StockDataFrame(
        get_1m_tencent().iloc[:20],
        date_col=TIME_KEY,
        time_frame='5m'
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
