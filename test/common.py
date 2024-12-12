from pathlib import Path
from datetime import (
    datetime,
    timedelta
)
from typing import Union
import numpy as np

from pandas import (
    DataFrame,
    Series,
    read_csv
)

from stock_pandas import StockDataFrame


simple_list = [2, 3, 4, 5, 6, 7]
names = 'abcdef'

TIME_KEY = 'time_key'
FORMAT = '%Y-%m-%d %H:%M:%S'
COLUMNS = ['open', 'high', 'low', 'close', 'volume']


csv = (Path(__file__).parent.parent / 'example' / 'tencent.csv').resolve()


def get_tencent(
    date_col: bool = True,
    stock: bool = True
) -> Union[StockDataFrame, DataFrame]:
    if not stock:
        return read_csv(csv)

    if date_col:
        return StockDataFrame(read_csv(csv), date_col='time_key')
    else:
        return StockDataFrame(read_csv(csv))


def get_1m_tencent(hour_offset: int = 0) -> DataFrame:
    """
    Change time index to 1-minute interval
    """

    df = get_tencent(stock=False)

    time_array = []
    date = datetime(2020, 1, 1, hour_offset)
    step = timedelta(minutes=1)

    for i in range(100):
        time_array.append(date.strftime(FORMAT))
        date += step

    # change time_key from day to minute
    df[TIME_KEY] = np.array(time_array)
    df = df[['time_key', *COLUMNS]]

    return df


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


def to_fixed(n: float, precision: int = 4):
    return format(n, f'.{precision}f')
