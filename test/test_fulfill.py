import pytest
from numpy import isnan
from pandas import DataFrame

from stock_pandas import (
    StockDataFrame
)

from .common import (
    get_tencent
)


@pytest.fixture
def tencent() -> StockDataFrame:
    return get_tencent(stock=True)


def test_fulfill(tencent: DataFrame):
    tencent = StockDataFrame(tencent)
    stock = tencent.iloc[:40]

    stock['ma:20']

    stock = stock.append(tencent.iloc[40])

    assert isnan(stock.iloc[40]['ma:20,close'])

    stock = stock.fulfill()

    row_41 = stock.iloc[40]

    assert row_41['ma:20,close'] == stock['ma:20'].iloc[40]
