from datetime import (
    datetime,
    timedelta
)

import pytest
from pandas import DataFrame
import numpy as np

from stock_pandas import (
    StockDataFrame,

)

from .common import (
    get_tencent
)


TIME_KEY = 'time_key'
FORMAT = '%Y-%m-%d %H:%M:%S'


@pytest.fixture
def tencent() -> DataFrame:
    df = get_tencent(stock=False)

    time_array = []
    date = datetime(2020, 1, 1)
    step = timedelta(minutes=1)

    for i in range(100):
        date += step
        time_array.append(date.strftime(FORMAT))

    # change time_key from day to minute
    df[TIME_KEY] = np.array(time_array)
    df = df[['time_key', 'open', 'high', 'low', 'close', 'volume']]

    return df


def test_cum_append_basic(tencent):
    stock = StockDataFrame(
        [],
        date_col=TIME_KEY,
        time_frame='5m'
    )

    stock = stock.cum_append(tencent.iloc[:1])

    assert stock.iloc[0]['open'] == 329.4

    stock_2 = stock.cum_append(tencent.iloc[1:2])

    assert stock.iloc[0]['open'] == 329.4

    assert stock_2.iloc[0]['open'] == 329.4
    assert stock_2.iloc[0]['high'] == 332.0
    assert stock_2.iloc[0]['low'] == 327.6
    assert stock_2.iloc[0]['close'] == 331.0
