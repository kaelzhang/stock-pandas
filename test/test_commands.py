import pytest
import numpy as np

from stock_pandas import StockDataFrame
from .common import (
    get_tencent,
    to_fixed
)


@pytest.fixture
def stock():
    return get_tencent()


def test_append(stock):
    """tests:
    - stock.append() -> StockDataFrame
    - we should calculate the right value of indicators
    - directive operator and surrounding whitespaces
    """

    current = stock[:'2020-02-04']  # type:ignore
    kdj_j = current['kdj.j'][-1]
    counter = -1

    max_len = len(stock)
    current_len = len(current)

    for i in range(current_len, max_len):
        current = current.append(stock.iloc[i])
        counter -= 1

        all_kdj_j = current['kdj.j']

        assert all_kdj_j[counter] == kdj_j

        assert type(current) is StockDataFrame

        if all_kdj_j[-1] < 0:
            # Test operator
            assert current['kdj.j<=0'][-1]
            assert current['kdj.j <0'][-1]
            assert not current['kdj.j == 0'][-1]

            break

    assert current['kdj.j>= 100']['2020-02-07']
    assert current['kdj.j > 100']['2020-02-07']

    assert str(current.iloc[-1].name) == '2020-02-24 00:00:00'


def test_cross(stock):
    assert stock['ma:10 >< ma:5']['2020-02-21']
    assert stock['ma:10 / ma:5']['2020-02-21']
    assert stock['ma:5 \\ ma:10']['2020-02-21']
    assert not stock['ma:10 \\ ma:5']['2020-02-21']


def test_increase(stock):
    assert stock['increase:close,3,1']['2020-02-13']
    assert type(stock.exec('increase:close,3', False)) is np.ndarray
    assert stock['increase:close,3']['2020-02-13']
    assert not stock['increase:close,4']['2020-02-13']
    assert stock['increase:close,3,-1']['2020-02-24']


def test_repeat(stock):
    stock = stock[:'2020-02-13']  # type: ignore

    assert stock['repeat:(style:bullish),1']['2020-02-13']
    assert stock['repeat:(style:bullish),2']['2020-02-13']
    assert stock['repeat:(style:bullish),6']['2020-02-13']
    assert not stock['repeat:(style:bullish),7']['2020-02-13']


def test_indexing(stock):
    assert type(stock[['kdj.k', 'kdj.d']]) is StockDataFrame


def test_column(stock):
    assert stock['column:close'][-1] == stock['close'][-1]


def test_boll(stock):
    assert stock['column:low < boll.lower']['2020-02-03']
    assert stock['column:open > boll.u']['2020-01-14']
    assert stock['column:close > boll']['2020-02-05']


def test_macd(stock):
    assert stock['macd / macd.dea']['2020-02-10']
    assert stock['macd.histogram / 0']['2020-02-10']


def test_rsi(stock):
    rsi6_80 = stock['rsi:6 > 80']
    assert rsi6_80['2020-02-13']
    assert not rsi6_80['2020-02-12']
    assert not rsi6_80['2020-02-14']


def test_bbi(stock):
    assert stock['repeat:(bbi < column:close),8']['2020-02-13']
    assert not stock['repeat:(bbi < column:close),9']['2020-02-13']


def test_kdj(stock):
    assert stock['kdj.j']['2020-02-07'] > 120
    assert stock['kdj.j']['2020-01-31'] < -1
    assert stock['kdj.j']['2020-02-24'] < -14

    kdjj = stock['kdj.j']['2020-02-07']
    assert stock['kdj.j:9,3,3,50']['2020-02-07'] == kdjj


def test_change(stock):
    change = stock['change:(column:close)']

    assert to_fixed(change[-1]) == '-0.0313'
    assert to_fixed(change[-2]) == '-0.0256'

    assert np.isnan(change[0])

    boll_change3 = stock['change:boll,3']

    assert to_fixed(boll_change3[-1]) == '-0.0030'
