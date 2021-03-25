import numpy as np
import itertools
import pytest
import pandas as pd

from stock_pandas import (
    StockDataFrame,
    directive_stringify
)

from .common import (
    simple_list,
    create_stock,
    get_stock_update
)


@pytest.fixture
def stock():
    return create_stock()


def test_directive_stringify(stock: StockDataFrame):
    assert stock.directive_stringify('boll') == 'boll:20,close'
    assert directive_stringify('boll') == 'boll:20,close'


def test_get_column(stock):
    stock = stock.rename(columns={
        'open': 'Open',
        'close': 'Close',
        'high': 'High',
        'low': 'Low'
    })

    with pytest.raises(
        KeyError,
        match='column "close" not found'
    ):
        stock.get_column('close')

    with pytest.raises(
        KeyError,
        match='column "close" not found'
    ):
        stock['ma:20']

    stock.alias('close', 'Close')

    # get_column should apply alias
    stock.get_column('close')


def test_astype(stock):
    stock = stock.astype({
        'open': 'float',
        'close': 'float'
    })

    assert isinstance(stock, StockDataFrame)

    open0 = stock.iloc[0]['open']
    assert isinstance(open0, float)


def test_indexing_by_callable(stock):
    assert isinstance(stock[lambda df: 'open'], pd.Series)


def test_ma(stock):
    stock.alias('Open', 'open')

    ma = stock['ma:2']

    stock = StockDataFrame(stock)

    list_ma0 = [3.5, 4.5, 5.5, 6.5, 7.5]

    assert np.isnan(ma[0])
    assert list(ma[1:]) == list_ma0

    new = get_stock_update()

    stock = stock.append(new, ignore_index=True)
    assert isinstance(stock, StockDataFrame)

    ma2 = stock.exec('ma:2')

    assert np.isnan(ma2[0])

    assert list(ma2[1:]) == [*list_ma0, 8.5]
    assert stock['Open'][0] == 2


COMMANDS = [
    'ma:{}',
    'macd.signal',
    'rsi:{}'
]


def test_period_larger_than_size(stock):
    period = len(stock) + 1

    for command in COMMANDS:
        directive_str = command.format(period)
        result = stock.exec(directive_str)

        assert np.all(
            np.isnan(result)
        ), directive_str


def test_aliases(stock):
    stock.alias('Open', 'open')
    assert list(stock['Open']) == simple_list

    with pytest.raises(ValueError, match='not exists'):
        stock.alias('some_column', 'not-exists')

    with pytest.raises(ValueError, match='already exists'):
        stock.alias('open', 'close')


def test_invalid_indexing(stock):
    with pytest.raises(KeyError, match='None'):
        stock[[1]]


def test_multi_index():
    tuples = list(itertools.product(
        ['foo', 'bar'],
        ['one', 'two']
    ))

    columns = pd.MultiIndex.from_tuples(tuples, names=['first', 'second'])

    with pytest.raises(ValueError, match='MultiIndex'):
        StockDataFrame(
            np.random.randn(3, 4),
            index=['A', 'B', 'C'],
            columns=columns
        )
