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


def check_append(head, new, ctor_twice=False):
    stock = StockDataFrame(head, date_col=TIME_KEY, copy=True)

    if ctor_twice:
        stock = StockDataFrame(stock)

    stock = stock.append(new)

    assert isinstance(stock, StockDataFrame)
    assert TIME_KEY not in stock.columns
    assert isinstance(stock.iloc[-1].name, Timestamp)

    if not ctor_twice:
        check_append(head, new, ctor_twice=True)


def check_append_no_time_key(head, new, ctor_twice=False, **kwargs):
    stock = StockDataFrame(head, date_col=TIME_KEY, copy=True)

    if ctor_twice:
        stock = StockDataFrame(stock)

    # Should not raise if new contains no TIME_KEY
    stock = stock.append(new, **kwargs)

    assert isinstance(stock, StockDataFrame)
    assert not isinstance(stock.iloc[-1].name, Timestamp)

    if not ctor_twice:
        check_append_no_time_key(head, new, ctor_twice=True, **kwargs)


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
    check_append(StockDataFrame(head), new)
    check_append(head, [new])
    check_append(StockDataFrame(head), [new])

    check_append_no_time_key(head, new, ignore_index=True)
    check_append_no_time_key(head, [new], ignore_index=True)

    head2 = head.copy()

    time_key2 = f'{TIME_KEY}2'
    head2[time_key2] = head2[TIME_KEY]

    head2 = StockDataFrame(head2, date_col=TIME_KEY)

    with pytest.raises(ValueError, match=time_key2):
        StockDataFrame(head2, date_col=time_key2)


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


# Github issue #22
def test_empty_df_append(tencent: DataFrame):
    stock = StockDataFrame(date_col=TIME_KEY)

    stock = stock.append(tencent)

    assert isinstance(stock, StockDataFrame)
    assert stock._cumulator._date_col == TIME_KEY


def test_append_meta(tencent: DataFrame):
    stock = StockDataFrame(tencent.iloc[:1], date_col=TIME_KEY)

    stock = stock.append(tencent)

    assert isinstance(stock, StockDataFrame)
    assert stock._cumulator._date_col == TIME_KEY
