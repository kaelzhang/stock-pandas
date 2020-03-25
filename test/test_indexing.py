# import numpy as np
# import itertools
import pytest
# import pandas as pd

from stock_pandas import StockDataFrame
from .common import (
    create_stock
)


@pytest.fixture
def stock():
    return create_stock().set_index('name')


def test_iloc(stock):
    stock = stock.iloc[1:]

    assert isinstance(stock, StockDataFrame)


def test_loc(stock):
    row = stock.iloc[1]
    stock = stock.loc[row.name:]

    assert isinstance(stock, StockDataFrame)

    assert stock.iloc[0].name == 'b'
