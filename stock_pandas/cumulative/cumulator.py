from typing import (
    Callable,
    Dict,
    Optional
)

from pandas import DataFrame

from stock_pandas.properties import KEY_CUMULATOR
from stock_pandas.common import set_attr

from .date import (
    apply_date,
    apply_date_to_df,
)

from .time_frame import (
    TimeFrame,
    TimeFrameArg
)


Cumulator = Callable[[float, float], float]
Cumulators = Dict[str, Cumulator]


def first(prev: float, _: float) -> float:
    return prev


def high(prev: float, current: float) -> float:
    return max(prev, current)


def low(prev: float, current: float) -> float:
    return min(prev, current)


def last(_: float, current: float) -> float:
    return current


def add(prev: float, current: float) -> float:
    return prev + current


class _Cumulator:
    CUMULATORS: Dict[str, Cumulator] = {
        'open': first,
        'high': high,
        'low': low,
        'close': last,
        'volume': add
    }

    def init(
        self,
        df,
        is_stock: bool,
        date_col: Optional[str],
        to_datetime_kwargs: dict,
        time_frame: TimeFrameArg,
        cumulators: Optional[Cumulators],
        # cumulate: bool
    ):
        self._date_col = date_col
        self._to_datetime_kwargs = to_datetime_kwargs
        self._time_frame = TimeFrame.ensure(time_frame)

        self._cumulators = (
            # None means use the default cumulators
            cumulators if cumulators is not None
            else self.CUMULATORS
        ).copy()

        if date_col:
            apply_date_to_df(df, date_col, to_datetime_kwargs)

    def add(self, column_name, cumulator: Cumulator):
        self._cumulators[column_name] = cumulator

    def append(
        self,
        df,
        other,
        *args, **kwargs
    ):
        if self._date_col is not None:
            other = apply_date(
                self._date_col,
                self._to_datetime_kwargs,
                True,
                other
            )

        return DataFrame.append(df, other, *args, **kwargs)


class CumulatorMixin:
    @property
    def _cumulator(self) -> _Cumulator:
        cumulator = getattr(self, KEY_CUMULATOR, None)

        if cumulator is None:
            cumulator = _Cumulator()
            set_attr(self, KEY_CUMULATOR, cumulator)

        return cumulator
