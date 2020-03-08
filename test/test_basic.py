import pandas as pd
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

    print('sma', sma)
    print('type sma', type(sma))

    new = pd.DataFrame(dict(
        open = [8],
        close = [9],
        high = [18],
        low = [7],
        volume = [800]
    ))

    stock = StockDataFrame(stock.append(new))

    print('>>>>>>>>>>', stock, type(stock))
    print(stock.calc('sma:2'))
    print(stock)

def test_aliases(stock):
    stock.alias('Open', 'open')

    assert list(stock['Open']) == l
