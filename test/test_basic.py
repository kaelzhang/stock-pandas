import pandas as pd

from stock_pandas import StockDataFrame

def test_basic_sma():
    l = [2, 3, 4, 5, 6, 7]

    data = pd.DataFrame({
        'open': l,
        'close': [x + 1 for x in l],
        'high': [x + 10 for x in l],
        'low': [x - 1 for x in l],
        'volume': [x * 100 for x in l]
    })

    stock = StockDataFrame.retype(data)

    print(stock)

    print(stock['sma:2'])
