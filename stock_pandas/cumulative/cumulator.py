from typing import (
    Callable,
    Dict,
    Optional
)

from numpy import ndarray
from pandas import (
    DataFrame,
    Series,
    concat
)

from stock_pandas.properties import KEY_CUMULATOR
from stock_pandas.common import set_attr

from .date import (
    apply_date,
    apply_date_to_df,
    ToBeAppended
)

from .time_frame import (
    TimeFrame,
    TimeFrameArg
)


Cumulator = Callable[[ndarray], float]
Cumulators = Dict[str, Cumulator]


def first(array: ndarray) -> float:
    return array[0]


def high(array: ndarray) -> float:
    return array.max()


def low(array: ndarray) -> float:
    return array.min()


def last(array: ndarray) -> float:
    return array[-1]


def add(array: ndarray) -> float:
    return array.sum()


def cum_append_type_error(date_col: Optional[str] = None) -> ValueError:
    message = 'the target to be `cum_append()`ed must have a DateTimeIndex'

    if date_col is None:
        return ValueError(message)

    return ValueError(f'{message} or a "{date_col}" column')


class _Cumulator:
    CUMULATORS: Dict[str, Cumulator] = {
        'open': first,
        'high': high,
        'low': low,
        'close': last,
        'volume': add
    }

    # The series to be cumulated
    _cum_series: Series

    def init(
        self,
        df,
        is_stock: bool,
        date_col: Optional[str],
        to_datetime_kwargs: dict,
        time_frame: TimeFrameArg,
        cumulators: Optional[Cumulators]
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

        self._unified_date_series = Series(dtype='int')

    def add(self, column_name, cumulator: Cumulator):
        self._cumulators[column_name] = cumulator

    def append(
        self,
        df,
        other: ToBeAppended,
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

    def _convert_to_date_dict(
        self,
        other: ToBeAppended
    ) -> dict:
        if isinstance(other, DataFrame):
            ...

    def cum_append(
        self,
        df,
        other: ToBeAppended,
        *args, **kwargs
    ):
        if self._time_frame is None:
            raise ValueError('time_frame must be specified before calling cum_append()')

        error = cum_append_type_error(self._date_col)

        other = self._apply_date(other, error)


class CumulatorMixin:
    @property
    def _cumulator(self) -> _Cumulator:
        cumulator = getattr(self, KEY_CUMULATOR, None)

        if cumulator is None:
            cumulator = _Cumulator()
            set_attr(self, KEY_CUMULATOR, cumulator)

        return cumulator
