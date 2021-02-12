import pytest
import numpy as np

from stock_pandas import StockDataFrame
from .common import (
    get_tencent
)


@pytest.fixture
def stock():
    return get_tencent(False)


def test_rolling_calc_backward(stock: StockDataFrame):
    hhv = stock.rolling_calc(
        5,
        'open',
        max
    )

    hhv_numpy = stock['hhv:5,open'].to_numpy()

    assert np.array_equal(hhv, hhv_numpy, equal_nan=True)


def test_rolling_calc_forward(stock: StockDataFrame):
    hhv = stock.rolling_calc(
        5,
        'open',
        max,
        True
    )

    start = 4

    hhv_numpy = stock['hhv:5,open'].to_numpy()

    assert np.array_equal(hhv[:-start], hhv_numpy[start:], equal_nan=True)
