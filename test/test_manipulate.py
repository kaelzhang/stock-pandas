import pytest

from stock_pandas import StockDataFrame
from .common import (
    get_tencent
)


@pytest.fixture
def stock():
    return get_tencent(False)


def test_drop(stock: StockDataFrame):
    origin = StockDataFrame(stock)

    stock['boll']

    name = stock.directive_stringify('boll')

    column_info_str = str(stock._stock_columns_info_map[name])
    assert 'size=100' in column_info_str
    assert 'lookback=19' in column_info_str

    last_boll = stock.iloc[-1][name]
    origin_last = stock.iloc[-1]

    last_index = len(origin) - 1

    stock = stock.drop([
        last_index
    ])

    stock = stock.append(origin_last)
    stock['boll']

    assert stock.iloc[-1][name] == last_boll

    stock = stock.drop([
        last_index
    ])

    new_last = origin_last.copy()
    new_last['open'] = 30
    new_last['high'] = 30
    new_last['low'] = 30
    new_last['close'] = 30

    stock = stock.append(new_last)

    stock['boll']

    assert stock.iloc[-1][name] != last_boll


def test_iloc_range(stock: StockDataFrame):
    stock['boll']

    name = stock.directive_stringify('boll')

    length = len(stock)

    last_boll = stock.iloc[-1][name]

    stock = stock.iloc[10:]

    assert isinstance(stock, StockDataFrame)

    assert stock.iloc[-1][name] == last_boll
    assert len(stock) == length - 10
