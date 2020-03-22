from stock_pandas import StockDataFrame

simple_list = [2, 3, 4, 5, 6, 7]


def create_stock():
    return StockDataFrame({
        'open': simple_list,
        'close': [x + 1 for x in simple_list],
        'high': [x + 10 for x in simple_list],
        'low': [x - 1 for x in simple_list],
        'volume': [x * 100 for x in simple_list]
    })
