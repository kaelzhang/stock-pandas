import pandas as pd

from stock_pandas import StockDataFrame

def test_basic_sma():
    l = [2, 3, 4, 5, 6, 7]

    # data = pd.DataFrame()

    stock = StockDataFrame({
        'open': l,
        'close': [x + 1 for x in l],
        'high': [x + 10 for x in l],
        'low': [x - 1 for x in l],
        'volume': [x * 100 for x in l]
    })

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

    stock = stock.append(new)

    print('>>>>>>>>>>', stock, type(stock))
