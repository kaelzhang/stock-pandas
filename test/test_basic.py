import numpy as np
import pytest

from stock_pandas import StockDataFrame
from .common import (
    simple_list,
    create_stock,
    get_stock_update
)


@pytest.fixture
def stock():
    return create_stock()


def test_astype(stock):
    stock = stock.astype({
        'open': 'float',
        'close': 'float'
    })

    assert isinstance(stock, StockDataFrame)

    open0 = stock.iloc[0]['open']
    assert isinstance(open0, float)


def test_ma(stock):
    stock.alias('Open', 'open')

    ma = stock['ma:2']

    stock = StockDataFrame(stock)

    list_ma0 = [3.5, 4.5, 5.5, 6.5, 7.5]

    assert np.isnan(ma[0])
    assert list(ma[1:]) == list_ma0

    new = get_stock_update()

    stock = stock.append(new, ignore_index=True)
    assert isinstance(stock, StockDataFrame)

    ma2 = stock.exec('ma:2')

    print(ma2)

    assert list(ma2[1:]) == [*list_ma0, 8.5]
    assert stock['Open'][0] == 2


def test_aliases(stock):
    stock.alias('Open', 'open')
    assert list(stock['Open']) == simple_list

    with pytest.raises(ValueError, match='not exists'):
        stock.alias('some_column', 'not-exists')

    with pytest.raises(ValueError, match='already exists'):
        stock.alias('open', 'close')


def test_invalid_indexing(stock):
    with pytest.raises(KeyError, match='None'):
        stock[[1]]
