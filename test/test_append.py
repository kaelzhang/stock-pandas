import pytest
from pandas import (
    DataFrame,
    Timestamp
)

from stock_pandas import (
    StockDataFrame
)

from .common import (
    get_tencent
)


TIME_KEY = 'time_key'


@pytest.fixture
def tencent() -> DataFrame:
    return get_tencent(stock=False)


def check_append(head, new):
    stock = StockDataFrame(head, date_col=TIME_KEY, copy=True)
    stock = stock.append(new)

    assert TIME_KEY not in stock.columns
    assert isinstance(stock.iloc[-1].name, Timestamp)


def check_append_no_time_key(head, new, **kwargs):
    stock = StockDataFrame(head, date_col=TIME_KEY, copy=True)

    # Should not raise if new contains no TIME_KEY
    stock = stock.append(new, **kwargs)

    assert not isinstance(stock.iloc[-1].name, Timestamp)


def test_append_without_date_col(tencent: DataFrame):
    head = tencent.iloc[:10]
    new = tencent.iloc[10]

    stock = DataFrame(head)
    stock = stock.append(new)

    assert stock.iloc[-1][TIME_KEY] == new[TIME_KEY]


def test_append_df(tencent: DataFrame):
    head = tencent.iloc[:10]
    new = tencent.iloc[10:15]

    check_append(head, new)
    check_append(head, [new])

    check_append_no_time_key(head, new, ignore_index=True)
    check_append_no_time_key(head, [new], ignore_index=True)


def test_append_df_without_time_key(tencent: DataFrame):
    head = tencent.iloc[:10]
    new = tencent.iloc[10:15].drop(columns=[TIME_KEY])
    check_append_no_time_key(head, new)
    check_append_no_time_key(head, [new])


def test_append_series(tencent: DataFrame):
    head = tencent.iloc[:10]
    new = tencent.iloc[10]

    check_append(head, new)
    check_append(head, [new])
    check_append(head, new.to_dict())
    check_append(head, [new.to_dict()])

    check_append_no_time_key(head, new, ignore_index=True)
    check_append_no_time_key(head, [new], ignore_index=True)
    check_append_no_time_key(head, new.to_dict(), ignore_index=True)
    check_append_no_time_key(head, [new.to_dict()], ignore_index=True)


def test_append_series_without_time_key(tencent: DataFrame):
    head = tencent.iloc[:10]
    new = tencent.iloc[10]
    new = new.drop(TIME_KEY)

    check_append_no_time_key(head, new)

    dic = new.to_dict()

    check_append_no_time_key(head, dic, ignore_index=True)
    check_append_no_time_key(head, [dic], ignore_index=True)


def test_append_invalid_type(tencent: DataFrame):
    stock = StockDataFrame(tencent, date_col=TIME_KEY, copy=True)

    with pytest.raises(TypeError, match='int'):
        stock.append(1)

    with pytest.raises(TypeError, match="list of <class 'int'>"):
        stock.append([1])

    with pytest.raises(TypeError, match="list of <class 'list'>"):
        stock.append([[]])
