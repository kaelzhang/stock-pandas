from stock_pandas import StockDataFrame
from pandas import DataFrame, Series

simple_list = [2, 3, 4, 5, 6, 7]
names = 'abcdef'


def create_stock():
    return StockDataFrame({
        'open': simple_list,
        'close': [x + 1 for x in simple_list],
        'high': [x + 10 for x in simple_list],
        'low': [x - 1 for x in simple_list],
        'volume': [x * 100 for x in simple_list],
        'name': [x for x in names]
    })


def get_stock_update():
    return DataFrame(dict(
        open=[8],
        close=[9],
        high=[18],
        low=[7],
        volume=[800],
        name=['g']
    ))


def get_last(series):
    index = len(series) - 1

    if isinstance(series, Series):
        series = series.to_numpy()

    return series[index]
