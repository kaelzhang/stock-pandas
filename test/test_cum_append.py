from datetime import (
    datetime,
    timedelta
)
import math

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
COLUMNS = ['open', 'high', 'low', 'close', 'volume']


@pytest.fixture
def tencent() -> DataFrame:
    """
    Change time index to 1-minute interval
    """

    df = get_tencent(stock=False)

    time_array = []
    date = datetime(2020, 1, 1)
    step = timedelta(minutes=1)

    for i in range(100):
        time_array.append(date.strftime(FORMAT))
        date += step

    # change time_key from day to minute
    df[TIME_KEY] = np.array(time_array)
    df = df[['time_key', *COLUMNS]]

    return df


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
            source = origin.iloc[i * 5: i * 5 + rest]
        else:
            source = origin.iloc[i * 5: (i + 1) * 5]

        series = cumulated.iloc[i]

        assert series['open'] == source['open'].to_numpy()[0]
        assert series['high'] == source['high'].to_numpy().max()
        assert series['low'] == source['low'].to_numpy().min()
        assert series['close'] == source['close'].to_numpy()[-1]
        assert series['volume'] == source['volume'].to_numpy().sum()


def test_cum_append_from_empty(tencent):
    stock = StockDataFrame(
        [],
        date_col=TIME_KEY,
        time_frame='5m'
    )

    for i in range(100):
        stock_new = stock.cum_append(tencent.iloc[i:i + 1])
        assert isinstance(stock, StockDataFrame)

        expect_cumulated(tencent, stock, i)
        expect_cumulated(tencent, stock_new, i + 1)

        stock = stock_new
