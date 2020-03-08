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
from stock_pandas import StockDataFrame
```

### StockDataFrame

`StockDataFrame` inherits from `pandas.DataFrame`, so if you are familiar with `pandas.DataFrame`, you are already ready to use `stock-pandas`

```py
import pandas as pd
stock = StockDataFrame(pd.read_csv('stock.csv'))
```

As we know, we could use `[]`, which called **pandas indexing** (a.k.a. `__getitem__` in python) to select out lower-dimensional slices. In addition to indexing with `colname` (column name of the `DataFrame`), we could also do indexing by `directive`s.

```py
stock[directive]

stock[[directive0, directive1]]
```

We have an example to show the most basic indexing using `[directive]`

```py
stock = StockDataFrame({
    'open' : ...,
    'high' : ...,
    'low'  : ...,
    'close': [5, 6, 7, 8, 9]
})

stock['sma:2']

# 0    NaN
# 3    5.5
# 4    6.5
# 5    7.5
# 0    8.5
# Name: sma:2,close, dtype: float64
```

Which prints the 2-period simple moving average on close column

## Syntax of `directive`

```ebnf
column_name := command_name | command_name operator expression
operator := '/' | '\' | '<' | '<=' | '==' | '>=' | '>' | '><'
expression := float | command_name
command_name := indicator | indicator : arguments
indicator := alphabets | alphabets.alphabets
arguments := string | arguments , string
```

#### `directive` Example

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

## Built-in Commands

### `sma`, simple moving averages

### `macd`

```py
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
```

### `boll`, bollinger bands

```py
# boll
stock['boll']

# bollinger upper band, a shortcut for stock['boll.upper']
stock['boll.u']
stock['boll.upper]

# bollinger lower band, which is equivalent to stock['boll.l']
stock['boll.lower']
stock['boll.l']
```

## Operators

- **`/`**:
- **`\`**:
- **`<`**:
- **`<=`**:
- **`==`**:
- **`>=`**:
- **`>`**:
- **`><`**:

****

## Advanced Sections
