from typing import List

from stock_pandas.common import period_to_int

from stock_pandas.directive.types import CommandArg


arg_period = CommandArg(coerce=period_to_int)
arg_period_14 = CommandArg(14, coerce=period_to_int)
arg_required = CommandArg()


def lookback_period(period: int, *args) -> int:
    return period - 1

def lookback_a_lot(period: int, *args) -> int:
    return period * 3

def create_series_args(series: List[str]) -> List[CommandArg]:
    return [CommandArg(default) for default in series]


series_close = create_series_args(['close'])
series_required = create_series_args([None])
