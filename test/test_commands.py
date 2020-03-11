
from pathlib import Path

import pytest
import pandas as pd

from stock_pandas import StockDataFrame

csv = (Path(__file__).parent.parent / 'example' / 'tencent.csv').resolve()

@pytest.fixture
def stock():
    return StockDataFrame(pd.read_csv(csv), date_column='time_key')

def test_append(stock):
    """tests:
    - stock.append() -> StockDataFrame
    - we should calculate the right value of indicators
    - directive operator and surrounding whitespaces
    """

    current = stock[:'2020-02-04']
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
    assert stock['increase:close,3']['2020-02-13']
    assert not stock['increase:close,4']['2020-02-13']


    # assert not stock['repeat:style:bullish,7']['2020-02-13']

def test_repeat(stock):
    stock = stock[:'2020-02-13']

    print(stock['style:bullish'][-10:])

    assert stock['repeat:style:bullish,1']['2020-02-13']
    assert stock['repeat:style:bullish,2']['2020-02-13']
    assert stock['repeat:style:bullish,6']['2020-02-13']
    assert not stock['repeat:style:bullish,7']['2020-02-13']
