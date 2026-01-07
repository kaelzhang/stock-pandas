from decimal import (
    Decimal,
    ROUND_DOWN
)
import pytest
import numpy as np

from stock_pandas import StockDataFrame
from .common import (
    get_tencent,
    to_fixed
)


@pytest.fixture
def stock():
    return get_tencent()


def test_append(stock):
    """tests:
    - stock.append() -> StockDataFrame
    - we should calculate the right value of indicators
    - directive operator and surrounding whitespaces
    """

    current = stock[:'2020-02-04']  # type:ignore
    kdj_j = current['kdj.j'].iloc[-1]
    counter = -1

    max_len = len(stock)
    current_len = len(current)

    for i in range(current_len, max_len):
        current = current.append(stock.iloc[i])
        counter -= 1

        all_kdj_j = current['kdj.j']

        assert all_kdj_j.iloc[counter] == kdj_j

        assert type(current) is StockDataFrame

        if all_kdj_j.iloc[-1] < 0:
            # Test operator
            assert current['kdj.j<=0'].iloc[-1], current['kdj.j<=0']
            assert not current['~(kdj.j<=0)'].iloc[-1], current['~(kdj.j<=0)']
            assert current['kdj.j <0'].iloc[-1]
            assert not current['kdj.j == 0'].iloc[-1]

            break

    assert current['kdj.j>= 100']['2020-02-07']
    assert current['kdj.j > 100']['2020-02-07']

    assert str(current.iloc[-1].name) == '2020-02-24 00:00:00'


def test_operators(stock):
    assert stock['(kdj.j > 100) | (kdj.j <= 100)'].to_numpy().all()
    assert stock['(kdj.j > 100) ^ (kdj.j <= 100)'].to_numpy().all()
    assert stock['(kdj.j < 200) & (kdj.j > -100)'].to_numpy().all()
    assert stock['kdj.j + 1 != kdj.j'].to_numpy().all()
    assert stock['kdj.j == kdj.j'].to_numpy().all()
    assert stock['(kdj.j - kdj.j) == 0'].to_numpy().all()
    assert stock['(kdj.j + - kdj.j) == 0'].to_numpy().all()

    assert np.array_equal(
        stock['kdj.j'].to_numpy() * 2,
        stock['kdj.j * 2'].to_numpy()
    )

    assert np.array_equal(
        stock['kdj.j'].to_numpy() / 2,
        stock['kdj.j / 2'].to_numpy()
    )


def test_cross(stock):
    assert stock['ma:10 >< ma:5']['2020-02-21']
    assert stock['ma:10 // ma:5']['2020-02-21']
    assert stock['ma:5 \\ ma:10']['2020-02-21']
    assert not stock['ma:10 \\ ma:5']['2020-02-21']


def test_increase(stock):
    assert stock['increase:3,1@close']['2020-02-13']
    assert type(stock.exec('increase:3@close', False)) is np.ndarray
    assert stock['increase:3@close']['2020-02-13']
    assert not stock['increase:4@close']['2020-02-13']
    assert stock['increase:3,-1@close']['2020-02-24']


def test_repeat(stock):
    stock = stock[:'2020-02-13']  # type: ignore

    assert stock['repeat:1@(style:bullish)']['2020-02-13']
    assert stock['repeat:2@(style:bullish)']['2020-02-13']
    assert stock['repeat:6@(style:bullish)']['2020-02-13']
    assert not stock['repeat:7@(style:bullish)']['2020-02-13']


def test_indexing(stock):
    assert type(stock[['kdj.k', 'kdj.d']]) is StockDataFrame


def test_boll(stock):
    assert stock['low < boll.lower']['2020-02-03']
    assert stock['open > boll.u']['2020-01-14']
    assert stock['close > boll']['2020-02-05']

    boll = stock['boll.upper']
    maboll = stock['ma:2@(boll.upper)']
    assert maboll.iloc[-1] == (boll.iloc[-1] + boll.iloc[-2]) / 2


def test_bbw(stock):
    a = stock['bbw'].to_numpy()
    b = (
        (stock['boll.upper'] - stock['boll.lower']) / stock['boll']
    ).to_numpy()

    for i in range(len(a)):
        assert to_fixed(a[i], 8) == to_fixed(b[i], 8), f'{i}: {a[i]} != {b[i]}'


def test_hv(stock):
    def apply_precision(value: float) -> Decimal:
        return Decimal(value).quantize(
            Decimal('0.000001'),
            rounding=ROUND_DOWN
        )

    assert apply_precision(stock['hv:20']['2020-03-09']) == Decimal('0.305508')
    assert apply_precision(
        stock['hv:20,1d,252']['2020-03-09']
    ) == Decimal('0.305508')


def test_donchian(stock):
    assert stock['donchian.upper:20'].equals(stock['hhv:20'])
    assert stock['donchian.lower:20'].equals(stock['llv:20'])
    assert stock['donchian:20'].equals(
        (stock['hhv:20'] + stock['llv:20']) / 2
    )


def test_macd(stock):
    assert stock['macd // macd.dea']['2020-02-10']
    assert stock['macd.histogram // 0']['2020-02-10']


def test_rsi(stock):
    rsi6_80 = stock['rsi:6 > 80']
    assert rsi6_80['2020-02-13']
    assert not rsi6_80['2020-02-12']
    assert not rsi6_80['2020-02-14']


def test_bbi(stock):
    assert stock['repeat:8@(bbi < close)']['2020-02-13']
    assert not stock['repeat:9@(bbi < close)']['2020-02-13']


def test_kdj(stock):
    assert stock['kdj.j']['2020-02-07'] > 120
    assert stock['kdj.j']['2020-01-31'] < -1
    assert stock['kdj.j']['2020-02-24'] < -14

    kdjj = stock['kdj.j']['2020-02-07']
    assert stock['kdj.j:9,3,3,50']['2020-02-07'] == kdjj


def test_change(stock):
    change = stock['change@close']

    assert to_fixed(change.iloc[-1]) == '-0.0313'
    assert to_fixed(change.iloc[-2]) == '-0.0256'

    assert np.isnan(change.iloc[0])

    boll_change3 = stock['change:3@(boll)']

    assert to_fixed(boll_change3.iloc[-1]) == '-0.0030'


def test_tr(stock):
    """Test TR (True Range) calculation."""
    tr = stock['tr']

    # TR should have all values (except first may be NaN in some edge cases)
    assert not np.isnan(tr.iloc[-1])

    # Verify TR is calculated correctly for a specific row
    # TR = max(high - low, |high - prev_close|, |low - prev_close|)
    idx = 10  # Pick a row to verify
    high = stock['high'].iloc[idx]
    low = stock['low'].iloc[idx]
    prev_close = stock['close'].iloc[idx - 1]
    expected_tr = max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close)
    )
    assert to_fixed(tr.iloc[idx], 4) == to_fixed(expected_tr, 4)


def test_atr(stock):
    assert 9.8 < stock['atr:14']['2020-03-06'] < 9.9


def test_ema(stock):
    """Test EMA (Exponential Moving Average) calculation."""
    ema20 = stock['ema:20']

    # EMA should have values after enough data points
    assert not np.isnan(ema20.iloc[-1])

    # EMA should be close to the price
    close = stock['close'].iloc[-1]
    assert abs(ema20.iloc[-1] - close) < close * 0.1  # Within 10%


def test_ma(stock):
    """Test MA (Simple Moving Average) calculation."""
    ma20 = stock['ma:20']

    # MA should have NaN for the first 19 values
    assert all(np.isnan(ma20.iloc[:19]))

    # MA should have values from index 19 onwards
    assert not np.isnan(ma20.iloc[19])

    # MA of last 20 values should equal the actual average
    close_last_20 = stock['close'].iloc[-20:].mean()
    assert to_fixed(ma20.iloc[-1]) == to_fixed(close_last_20)
