from stock_pandas import StockDataFrame
import pandas as pd

simple_list = [2, 3, 4, 5, 6, 7]


def create_stock():
    return StockDataFrame({
        'open': simple_list,
        'close': [x + 1 for x in simple_list],
        'high': [x + 10 for x in simple_list],
        'low': [x - 1 for x in simple_list],
        'volume': [x * 100 for x in simple_list]
    })


def get_stock_update():
    return pd.DataFrame(dict(
        open=[8],
        close=[9],
        high=[18],
        low=[7],
        volume=[800]
    ))


def get_last(stock):
    return stock[len(stock) - 1]
