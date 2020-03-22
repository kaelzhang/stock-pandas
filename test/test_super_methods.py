import pytest

from stock_pandas import StockDataFrame
from .common import (
    create_stock
)


@pytest.fixture
def stock():
    return create_stock()


def test_drop(stock):
    after_dropped = stock.drop([0])

    assert isinstance(after_dropped, StockDataFrame)

    assert len(after_dropped) == 5
