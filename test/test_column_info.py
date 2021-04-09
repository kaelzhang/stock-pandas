from stock_pandas import (
    StockDataFrame
)

from .common import (
    get_1m_tencent,
    TIME_KEY
)


def test_cum_append_feat_indicator():
    tencent = get_1m_tencent()

    stock = StockDataFrame(
        tencent.iloc[:19],
        date_col=TIME_KEY,
        time_frame='5m'
    ).cumulate()

    ma = stock['ma:2'][-1]

    assert ma == stock.iloc[-2:]['close'].sum() / 2

    stock = stock.cum_append(tencent.iloc[19:20])
    assert stock._stock_columns_info_map['ma:2,close'].size == len(stock) - 1

    new_ma = stock['ma:2'][-1]

    assert ma != new_ma

    stock = StockDataFrame(
        stock,
        time_frame='15m'
    )

    assert stock._stock_columns_info_map['ma:2,close'].size == len(stock)

    stock = stock.cum_append(tencent.iloc[20:21])
    assert stock._stock_columns_info_map['ma:2,close'].size == len(stock) - 1

    stock = stock.cumulate()

    # Time frame changed, so info map should not be inherited
    assert 'ma:2,close' not in stock._stock_columns_info_map


def test_indexing():
    tencent = get_1m_tencent()

    stock = StockDataFrame(tencent)

    stock['ma:2']

    stock = stock[stock['close'] > stock['close'].mean()]

    print(stock._stock_columns_info_map)
