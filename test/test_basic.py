import numpy as np
import itertools
import pytest
import pandas as pd

from stock_pandas import (
    StockDataFrame
)

from .common import (
    simple_list,
    create_stock,
    get_stock_update,
    get_tencent
)


@pytest.fixture
def stock():
    return create_stock()


def test_directive_stringify(stock: StockDataFrame):
    assert StockDataFrame.directive_stringify('boll') == 'boll'
    assert StockDataFrame.directive_stringify('boll:30@close') == 'boll:30'


def test_exec(stock):
    result = stock.exec('close')
    close = stock['close'].to_numpy()

    assert np.all(result == close)


def test_get_column(stock):
    stock = stock.rename(columns={
        'open': 'Open',
        'close': 'Close',
        'high': 'High',
        'low': 'Low'
    })

    message = 'column "close" not found'

    with pytest.raises(
        KeyError,
        match=message
    ):
        stock.get_column('close')

    with pytest.raises(
        KeyError,
        match=message
    ):
        stock['ma:20']

    # It is ok to specify the close column
    stock['ma:20@Close']

    stock.alias('close', 'Close')

    # get_column should apply alias
    stock.get_column('close')


def test_copy(stock):
    stock['ma:2']

    def ma_size(stock):
        return stock._stock_columns_info_map.get('ma:2').size

    assert ma_size(stock) == ma_size(stock.copy())


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

    mama2 = stock['ma:2@(ma:2)']

    assert mama2.iloc[-1] == (ma2[-1] + ma2[-2]) / 2

    stock['change@(ma:5@(boll.upper:21,2))']


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

    dropped = stock.drop(columns=['close'])
    assert list(dropped['Open']) == simple_list

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


def test_date_col_pollution_issue_21():
    csv = get_tencent(stock=False)

    StockDataFrame(csv, date_col='time_key')

    # The issue of the pandas is fixed, so this test is not needed
    # with pytest.raises(KeyError, match='time_key'):
    #     csv['time_key']

    csv = get_tencent(stock=False)

    StockDataFrame(csv, date_col='time_key', copy=True)

    try:
        csv['time_key']
    except Exception as e:
        raise RuntimeError(f'date_col should not change the original dataframe, error: {e}')


def test_lookback(stock):
    # (directive, expected_lookback)
    cases = [
        # Trend-following: ma, ema (lookback = period - 1)
        ('ma:5', 4), ('ema:5', 4),
        # MACD variants
        ('macd', 25), ('macd.signal', 33), ('macd.histogram', 33),
        # BBI (lookback = max of all periods)
        ('bbi', 24),
        # TR & ATR
        ('tr', 1), ('atr', 14),
        # LLV, HHV, Donchian (lookback = period - 1)
        ('llv:5', 4), ('hhv:5', 4), ('donchian:5', 4),
        # RSV & KDJ
        ('rsv:9', 8), ('kdj.k', 27), ('kdj.d', 27), ('kdj.j', 27),
        # RSI (lookback = period, due to diff + SMMA warmup)
        ('rsi', 14),
        # Bollinger Bands (lookback = period - 1)
        ('boll', 19), ('boll.upper', 19), ('boll.lower', 19), ('bbw', 19),
        # Historical Volatility (lookback = period, due to log return)
        ('hv:20', 20),
        # Tools
        ('increase:1@close', 0), ('style:bullish', 0),
        ('repeat:2@(style:bullish)', 1), ('change:2@close', 1),
        # Compound directives: lookback = base_lb + series_lb
        # repeat:5@(close > boll.upper) = (5-1) + max(0, 20-1) = 4 + 19 = 23
        ('repeat:5@(close > boll.upper)', 23),
        # repeat:3@(ma:10 > ma:20) = (3-1) + max(10-1, 20-1) = 2 + 19 = 21
        ('repeat:3@(ma:10 > ma:20)', 21),
        # --- Additional cases with varying parameters ---
        # MA/EMA: lookback = period - 1 (need N points for N-period average)
        ('ma:10', 9), ('ma:20', 19), ('ema:12', 11), ('ema:26', 25),
        # MACD: lookback = max(fast, slow) - 1
        # MACD.signal: lookback = max(fast, slow) + signal - 2
        ('macd:5,10', 9), ('macd.signal:5,10,3', 11), ('macd.histogram:8,17,5', 20),
        # BBI: lookback = max(a, b, c, d), all MAs must be valid
        ('bbi:5,10,15,20', 20),
        # ATR/RSI: lookback = period (TR needs prev close; RSI needs SMMA warmup)
        ('atr:7', 7), ('rsi:7', 7),
        # Bollinger: lookback = period - 1 (MA + std need N points)
        ('boll:10', 9), ('boll.upper:30,2.5', 29),
        # KDJ: lookback = period * 3 (EWMA needs longer warmup for stability)
        ('kdj.k:5,3,50', 15), ('kdj.d:14,5,5,50', 42),
        # HV: lookback = period (log returns need period price changes)
        ('hv:10', 10), ('hv:30', 30),
    ]
    for directive, expected in cases:
        assert (
            StockDataFrame.directive_lookback(directive) == expected
        ), f'{directive} lookback mismatch'
