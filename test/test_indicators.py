
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

    max_len = len(stock)
    current_len = len(current)

    for i in range(current_len, max_len):
        current = current.append(stock.iloc[i])

        assert type(current) is StockDataFrame

        if current['kdj.j'][-1] < 0:
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
