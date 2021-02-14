from stock_pandas.dataframe import StockDataFrame
import pytest

from .common import (
    create_stock,
    get_last,
    get_stock_update
)


@pytest.fixture
def stock():
    return create_stock()


def test_drop(stock):
    assert get_last(stock['ma:2']) == 7.5
    assert get_last(stock['ma:2,high']) == 16.5

    stock['ma:2,open']

    stock = stock.drop(index=[0, 1, 2], columns=['open', 'ma:2,open'])

    columns_info_map = stock._stock_columns_info_map

    assert 'open' not in columns_info_map

    assert 'ma:2,open' not in columns_info_map, 'columns should be cleaned'

    stock = stock.append(get_stock_update())

    print(stock)

    assert get_last(stock['ma:2']) == 8.5
    assert get_last(stock['ma:2,high']) == 17.5


def test_slice(stock):
    assert get_last(stock['ma:2']) == 7.5

    stock = stock[5:]

    assert stock._stock_columns_info_map['ma:2,close'].size == 1

    stock = stock.append(get_stock_update())

    assert get_last(stock['ma:2']) == 8.5


def test_iloc_slice(stock):
    assert get_last(stock['ma:2']) == 7.5

    stock = stock.iloc[5:]
    stock = stock.append(get_stock_update())

    assert get_last(stock['ma:2']) == 8.5


def test_slice_with_object(stock: StockDataFrame):
    stock['ma:2']

    stock = stock.iloc[1:5]

    assert stock._stock_columns_info_map['ma:2,close'].size == 4


def test_slice_with_step(stock: StockDataFrame):
    stock['ma:2']

    stock = stock.iloc[0::2]

    assert stock._stock_columns_info_map['ma:2,close'].size == 0


def test_invalid_slicing(stock: StockDataFrame):
    with pytest.raises(AssertionError):
        # However, it might never happen,
        # but there is a assertion in super()._slice
        # we have to test about this case
        stock._slice({})

    assert stock._stock_indexer_slice is None
