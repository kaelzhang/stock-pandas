from typing import (
    Callable,
    Dict,
    List,
    Optional
)

from numpy import ndarray
from pandas import (
    DataFrame,
    Series,
    concat
)
from pandas._libs.tslibs import Timestamp

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

    _to_be_cumulated: Optional[DataFrame]
    _to_be_appended: List[Series]

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

        if date_col is not None:
            self._to_datetime_kwargs = to_datetime_kwargs

            apply_date_to_df(df, date_col, to_datetime_kwargs)

        self._time_frame = TimeFrame.ensure(time_frame)

        if self._time_frame is None:
            return

        self._cumulators = (
            # None means use the default cumulators
            cumulators if cumulators is not None
            else self.CUMULATORS
        ).copy()

        # TODO:
        # check the type of self._to_be_cumulated
        self._to_be_cumulated = None
        self._to_be_cumulated_inited = False
        self._to_be_appended = []

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

    def cum_append(
        self,
        df,
        # TODO:
        # support other types
        other: DataFrame,
        *args, **kwargs
    ):
        if self._time_frame is None:
            raise ValueError('time_frame must be specified before calling cum_append()')

        if not len(other):
            raise ValueError('the data frame to be appended is empty')

        other = self._convert_to_date_df(other)

        last_timestamp = (
            None if self._to_be_cumulated is None
            else self._to_be_cumulated.iloc[-1].name
        )

        start = None
        last = None

        for timestamp in other.index:
            if not isinstance(timestamp, Timestamp):
                raise cum_append_type_error(self._date_col)

            if start is None:
                start = timestamp

            if last_timestamp is None:
                last_timestamp = timestamp
                continue

            if (
                self._time_frame.unify(last_timestamp)
                != self._time_frame.unify(timestamp)
            ):
                self._cumulate(
                    None if last is None else other[start:last]
                )

                start = timestamp

            last = timestamp

        self._to_be_cumulated = other[start:]

        # Append the rows even the latest time frame is not closed
        self._append_to_be_appended(self._to_be_cumulated)

        return self._append(df)

    def _convert_to_date_df(
        self,
        other: DataFrame
    ) -> DataFrame:
        date_col = self._date_col
        to_datetime_kwargs = self._to_datetime_kwargs

        if date_col is not None and date_col in other.columns:
            other = other.copy()
            apply_date_to_df(other, date_col, to_datetime_kwargs)

        return other

    def _cumulated(
        self,
        to_be_cumulated: Optional[DataFrame]
    ):
        to_be_cumulated = [
            item
            for item in [to_be_cumulated, self._to_be_cumulated]
            if item is not None
        ]
        self._to_be_cumulated = None

        if not to_be_cumulated:
            return

        if len(to_be_cumulated) == 2:
            to_be_cumulated = concat(to_be_cumulated)

        self._append_to_be_appended(to_be_cumulated)

    def _append_to_be_appended(self, to_be_cumulated: DataFrame):
        if len(to_be_cumulated) == 1:
            self._to_be_appended.append(to_be_cumulated)
            return

        # Use the values of the last row except columns of self._cumulators
        to_be_appended = to_be_cumulated.iloc[-1].copy()

        # Use the index of the first row
        to_be_appended.rename(to_be_cumulated.iloc[0].name)

        for column_name in to_be_appended.columns:
            cumulator = self._cumulators.get(column_name)

            if cumulator is not None:
                to_be_appended[column_name] = cumulator(
                    to_be_appended[column_name].to_numpy()
                )

        self._to_be_appended.append(to_be_appended)

    def _append(self, df):
        timestamp = self._to_be_appended[0].name

        duplicates = df[timestamp:]

        return df.drop(duplicates.index).append(self._to_be_appended)


class CumulatorMixin:
    @property
    def _cumulator(self) -> _Cumulator:
        cumulator = getattr(self, KEY_CUMULATOR, None)

        if cumulator is None:
            cumulator = _Cumulator()
            set_attr(self, KEY_CUMULATOR, cumulator)

        return cumulator
