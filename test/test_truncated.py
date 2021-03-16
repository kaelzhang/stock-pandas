from stock_pandas.dataframe import StockDataFrame
import pytest
import numpy as np

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


def test_slice_with_negative_start(stock: StockDataFrame):
    stock['ma:2']

    stock = stock.iloc[-2:]
    stock = stock.drop(columns=['name'])

    assert stock._stock_columns_info_map['ma:2,close'].size == 2
    assert not np.isnan(stock.values).any()


def test_slice_with_negative_end(stock: StockDataFrame):
    stock['ma:2']
    length = len(stock)

    stock = stock.iloc[:-2]
    stock = stock.drop(columns=['name'])

    assert stock._stock_columns_info_map['ma:2,close'].size == length - 2
    assert np.isnan(stock.values).any()


def test_invalid_slicing(stock: StockDataFrame):
    with pytest.raises(AssertionError):
        # However, it might never happen,
        # but there is a assertion in super()._slice
        # we have to test about this case
        stock._slice({})

    assert stock._stock_indexer_slice is None


def test_columns_manipulate(stock: StockDataFrame):
    stock = stock.drop(columns=['name'])

    indicators = ['ma:2', 'ma:2,open']

    columns_names = [
        stock.directive_stringify(indicator)
        for indicator in indicators
    ]

    for indicator in indicators:
        stock[indicator]

    stock = stock.iloc[1:]
    stock = stock[columns_names + ['open']]

    assert not np.isnan(stock.values).any()
