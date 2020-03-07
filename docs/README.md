[![](https://travis-ci.org/kaelzhang/stock-pandas.svg?branch=master)](https://travis-ci.org/kaelzhang/stock-pandas)
[![](https://codecov.io/gh/kaelzhang/stock-pandas/branch/master/graph/badge.svg)](https://codecov.io/gh/kaelzhang/stock-pandas)
[![](https://img.shields.io/pypi/v/stock-pandas.svg)](https://pypi.org/project/stock-pandas/)
[![](https://img.shields.io/pypi/l/stock-pandas.svg)](https://github.com/kaelzhang/stock-pandas)

# stock-pandas

The wrapper of `pandas.DataFrame` with stock statistics and indicators support for automatical trading

## Install

```sh
pip install stock-pandas
```

## Usage

```py
import pandas as pd

from stock_pandas import StockDataFrame
```

### StockDataFrame

```py
stock = StockDataFrame.retype(pd.read_csv('stock.csv'))
```

#### Syntax of Column Name

```ebnf
column_name := command_name | command_name operator expression
operator := '/' | '\' | '<' | '<=' | '==' | '>=' | '>' | '><'
expression := float | command_name
command_name := indicator | indicator : arguments
indicator := alphabets | alphabets.alphabets
arguments := string | arguments , string
```

#### Column Name Example

Here lists several use cases of column names

```py
# The 20-day(default) moving average
#   which is the mid band of bollinger bands
stock['boll']

# kdjj less than 0
stock['kdj.j < 0']

# 9-day kdjk cross up 3-day kdjd
stock['kdj.k:9 / kdj.d:3']

# 5-day simple moving average
stock['sma:5']

# 10-day simple moving average on open prices
stock['sma:10,open']
```

```
# macd
stock['macd']
stock['macd.dif']

# macd signal band, which is a shortcut for stock['macd.signal']
stock['macd.s']
stock['macd.signal']
stock['macd.dea']

# macd histogram band, which is equivalent to stock['macd.h']
stock['macd.histogram']
stock['macd.h']
stock['macd.macd']

# boll
stock['boll']

# bollinger upper band, a shortcut for stock['boll.upper']
stock['boll.u']
stock['boll.upper]

# bollinger lower band, which is equivalent to stock['boll.l']
stock['boll.lower']
stock['boll.l']
```
