import math

import pytest
from pandas import DataFrame


from stock_pandas import (
    StockDataFrame,

)

from .common import (
    get_tencent,
    get_1m_tencent,
    TIME_KEY
)


LENGTH = 20


@pytest.fixture()
def tencent():
    return get_1m_tencent().iloc[:LENGTH]


def expect_cumulated(
    origin,
    cumulated,
    n_appended,
    step=5
):
    length = len(cumulated)

    assert length == math.ceil(n_appended / step), f'length not match for {n_appended}'

    if n_appended == 0:
        return

    rest = n_appended % step

    for i in range(length):
        if i == length - 1 and rest:
            source = origin.iloc[i * step: i * step + rest]
        else:
            source = origin.iloc[i * step: (i + 1) * step]

        series = cumulated.iloc[i]

        assert series['open'] == source['open'].to_numpy()[0]
        assert series['high'] == source['high'].to_numpy().max()
        assert series['low'] == source['low'].to_numpy().min()
        assert series['close'] == source['close'].to_numpy()[-1]
        assert series['volume'] == source['volume'].to_numpy().sum()


def test_cum_append_from_empty(tencent):
    stock = StockDataFrame(
        date_col=TIME_KEY,
        time_frame='5m'
    )

    for i in range(LENGTH):
        stock_new = stock.cum_append(tencent.iloc[i:i + 1])
        assert isinstance(stock, StockDataFrame)

        expect_cumulated(tencent, stock, i)
        expect_cumulated(tencent, stock_new, i + 1)
        expect_cumulated(
            tencent,
            StockDataFrame(
                date_col=TIME_KEY,
                time_frame='5m'
            ).cum_append(
                tencent.iloc[:i + 1]
            ),
            i + 1
        )

        stock = stock_new


def test_cum_append_many_from_empty(tencent):
    stock = StockDataFrame(
        date_col=TIME_KEY,
        time_frame='5m'
    ).cum_append(tencent.iloc[:LENGTH])

    expect_cumulated(
        tencent,
        stock,
        LENGTH
    )


def test_cumulate(tencent):
    stock = StockDataFrame(
        tencent,
        date_col=TIME_KEY,
        time_frame='5m'
    ).cumulate()

    expect_cumulated(tencent, stock, LENGTH)

    assert stock.equals(stock.cumulate())


def test_cum_append_error():
    tencent = get_tencent(stock=False)

    with pytest.raises(ValueError, match='time_frame'):
        StockDataFrame().cum_append(
            tencent.iloc[:1]
        )

    with pytest.raises(ValueError, match='empty'):
        StockDataFrame(time_frame='5m').cum_append(
            DataFrame()
        )

    with pytest.raises(ValueError, match='DatetimeIndex'):
        StockDataFrame(time_frame='5m').cum_append(
            tencent.iloc[:1]
        )

    with pytest.raises(ValueError, match='non-exists'):
        StockDataFrame(date_col='non-exists', time_frame='5m').cum_append(
            tencent.iloc[:1]
        )


def test_cum_append_feat_indicator(tencent):
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
