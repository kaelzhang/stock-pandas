import pytest

from .common import (
    get_tencent
)


@pytest.fixture
def stock():
    return get_tencent()


def test_append(stock):
    stock0 = stock.iloc[0:-4]
    stock1 = stock.iloc[-4:-3]
    stock2 = stock.iloc[-3:-2]
    stock3 = stock.iloc[-2:-1]
    stock4 = stock.iloc[-1:]
    stock = stock0

    index = -1
    j = stock['kdj.j'][index]

    for s in [stock1, stock2, stock3, stock4]:
        index -= 1

        stock = stock.append(s)
        assert stock['kdj.j'][index] == j
