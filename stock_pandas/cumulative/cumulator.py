from typing import (
    # Callable,
    Optional
)

from pandas import DataFrame

from stock_pandas.properties import KEY_CUMULATOR
from stock_pandas.common import set_attr

from .date import (
    apply_date,
    apply_date_to_df,
)


# Cumulator = Callable[[float, float], float]


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


class Cumulator:
    def init(
        self,
        df,
        is_stock: bool,
        date_col: Optional[str],
        to_datetime_kwargs: dict
    ):
        self._date_col = date_col
        self._to_datetime_kwargs = to_datetime_kwargs

        if date_col:
            apply_date_to_df(df, date_col, to_datetime_kwargs)

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
    def cumulator(self) -> Cumulator:
        cumulator = getattr(self, KEY_CUMULATOR, None)

        if cumulator is None:
            cumulator = Cumulator()
            set_attr(self, KEY_CUMULATOR, cumulator)

        return cumulator
