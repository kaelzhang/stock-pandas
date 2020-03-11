
from pathlib import Path

import pytest
import pandas as pd

from stock_pandas import StockDataFrame

csv = (Path(__file__).parent.parent / 'example' / 'tencent.csv').resolve()

@pytest.fixture
def stock():
    return StockDataFrame(pd.read_csv(csv), date_column='time_key')

def test_append(stock):
    current = stock[:'2020-02-04']

    print(current['kdj.j'])

    max_len = len(stock)
    current_len = len(current)

    for i in range(current_len, max_len):
        pass
