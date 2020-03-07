[![](https://travis-ci.org/kaelzhang/stock-pandas.svg?branch=master)](https://travis-ci.org/kaelzhang/stock-pandas)
[![](https://codecov.io/gh/kaelzhang/stock-pandas/branch/master/graph/badge.svg)](https://codecov.io/gh/kaelzhang/stock-pandas)
[![](https://img.shields.io/pypi/v/stock-pandas.svg)](https://pypi.org/project/stock-pandas/)
[![](https://img.shields.io/pypi/l/stock-pandas.svg)](https://github.com/kaelzhang/stock-pandas)

# stock-pandas

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

For example

```py
stock['kdj.k']

# kdjj less than 0
stock['kdj.j < 0']

# 9-day kdjk cross up 3-day kdjd
stock['kdj.k:9 / kdj.d:3']

# 5-day simple moving average
stock['sma:5']

stock['macd.s']

stock['boll']

stock['boll.u']
```

