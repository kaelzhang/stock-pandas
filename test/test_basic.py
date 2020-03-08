import pandas as pd
import numpy as np
import pytest

from stock_pandas import StockDataFrame

l = [2, 3, 4, 5, 6, 7]

@pytest.fixture
def stock():
    return StockDataFrame({
        'open': l,
        'close': [x + 1 for x in l],
        'high': [x + 10 for x in l],
        'low': [x - 1 for x in l],
        'volume': [x * 100 for x in l]
    })

def test_basic_sma(stock):
    sma = stock['sma:2']

    stock = StockDataFrame(stock)

    list_sma0 = [3.5, 4.5, 5.5, 6.5, 7.5]

    assert np.isnan(sma[0])
    assert list(sma[1:]) == list_sma0

    new = pd.DataFrame(dict(
        open = [8],
        close = [9],
        high = [18],
        low = [7],
        volume = [800]
    ))

    stock = stock.append(new)
    sma2 = stock.calc('sma:2')

    assert list(sma2[1:]) == [*list_sma0, 8.5]


def test_aliases(stock):
    stock.alias('Open', 'open')
    assert list(stock['Open']) == l
