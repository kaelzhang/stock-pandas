[![](https://travis-ci.org/kaelzhang/stock-pandas.svg?branch=master)](https://travis-ci.org/kaelzhang/stock-pandas)
[![](https://codecov.io/gh/kaelzhang/stock-pandas/branch/master/graph/badge.svg)](https://codecov.io/gh/kaelzhang/stock-pandas)
[![](https://img.shields.io/pypi/v/stock-pandas.svg)](https://pypi.org/project/stock-pandas/)
[![](https://img.shields.io/pypi/l/stock-pandas.svg)](https://github.com/kaelzhang/stock-pandas)

# stock-pandas

A wrapper and a subtle class of `pandas.DataFrame` which supports:
- stock statistics
- all kinds of stock indicators

`stock-pandas` makes automatical trading much easier. `stock-pandas` requires Python >= **3.6**

With the help of `stock-pandas` and mplfinance, we could easily draw something like:

![](boll.png)

The code example is available at [here](https://github.com/kaelzhang/stock-pandas/blob/master/example/bollinger_bands.ipynb).

## Install

```sh
pip install stock-pandas
```

## Usage

```py
from stock_pandas import StockDataFrame
```

We also have some examples with annotations in the [`example`](https://github.com/kaelzhang/stock-pandas/tree/master/example) directory, you could use [JupyterLab](https://jupyter.org/) or Jupyter notebook to play with them.

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

stock['ma:2']

# 0    NaN
# 1    5.5
# 2    6.5
# 3    7.5
# 4    8.5
# Name: ma:2,close, dtype: float64
```

Which prints the 2-period simple moving average on column `"close"`.

#### stock.calc(directive: str, create_column: bool=False) -> Series

Calculates series according to the directive.

```py
stock['ma:2']
# is equivalent to:
stock.calc('ma:2', create_column=True)
```

```py
# This will only calculate without creating a new column in the dataframe
stock.calc('ma:20')
```

#### stock.alias(alias: str, name: str) -> None

Defines column alias or directive alias

- **alias** `str` the alias name
- **name** `str` the name of an existing column or the directive string

```py
# Some plot library such as `mplfinance` requires a column named capitalized `Open`,
# but it is ok, we could create an alias.
stock.alias('Open', 'open')

stock.alias('buy_point', 'kdj.j < 0')
```

## Syntax of `directive`

```ebnf
directive := command | command operator expression
operator := '/' | '\' | '><' | '<' | '<=' | '==' | '>=' | '>'
expression := float | command

command := command_name | command_name : arguments
command_name := main_command_name | main_command_name.sub_command_name
main_command_name := alphabets
sub_command_name := alphabets

arguments := argument | argument , arguments
argument := string | ( arguments )
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
stock['ma:5']

# 10-day simple moving average on open prices
stock['ma:10,open']
```

## Built-in Commands

Document syntax explanation:

- **param** `str` which means a required parameter of type `str`.
- **param?** `str='close'` which means parameter `param` is optional with default value `'close'`.

### `ma`, simple Moving Averages

```
ma:<period>,<column>
```

Gets the `period`-period simple moving average on column named `column`.

`SMA` is often confused between simple moving average and smoothed moving average.

So `stock-pandas` will use `ma` for simple moving average and `smma` for smoothed moving average.

- **period** `int` (required)
- **column?** `str='close'` Which column should the calculation based on. Defaults to `'close'`

```py
# which is equivalent to `stock['ma:5,close']`
stock['ma:5']

stock['ma:10,open']
```

### `macd`, Moving Average Convergence Divergence

```
macd:<fast_period>,<slow_period>
macd.signal:<fast_period>,<slow_period>,<signal_period>
macd.histogram:<fast_period>,<slow_period>,<signal_period>
```

- **fast_period?** `int=26` fast period. Defaults to `26`.
- **slow_period?** `int=12` slow period. Defaults to `12`
- **signal_period?** `int=9` signal period. Defaults to `9`

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

### `boll`, BOLLinger bands

```
boll:<period>,<times>,<column>
```

- **period?** `int=20`
- **times?** `int=2`
- **column?** `str='close'`

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

### `kdj`, stochastic oscillator

```
kdj.k:<param_k>
kdj.d:<param_d>
kdj.j:<param_j>
```

- **param_k?** `int=9`
- **param_d?** `int=9`
- **param_j?** `int=9`

```py
# The k series of KDJ 999
stock['kdj.k']

# The KDJ serieses of with parameters 9, 3, and 3
stock[['kdj.k', 'kdj.d:3', 'kdj.j:3']]
```

## Operators

```
left operator right
```

- **`/`**: whether `left` crosses through `right` from the down side of `right` to the upper side which we call it as "cross up".
- **`\`**: whether `left` crosses down `right`.
- **`><`**: whether `left` crosses `right`.
- **`<`** / **`<=`** / **`==`** / **`>=`** / **`>`**: For a certain record of the same time, whether the value of `left` is less than / less than or equal to / equal to / larger than or equal to / larger than the value of `right`.

****

## Advanced Sections
