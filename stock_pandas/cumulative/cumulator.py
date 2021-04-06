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
ToAppend = List[Series]


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


def append(
    df: DataFrame,
    to_append: ToAppend,
    *args, **kwargs
):
    timestamp = to_append[0].name

    duplicates = df[timestamp:]

    return df.drop(duplicates.index).append(to_append, *args, **kwargs)


class _Cumulator:
    CUMULATORS: Dict[str, Cumulator] = {
        'open': first,
        'high': high,
        'low': low,
        'close': last,
        'volume': add
    }

    _to_cumulate: Optional[DataFrame]

    def __repr__(self) -> str:
        return f'<Cumulator date_col:{self._date_col}, time_frame:{self._time_frame}>'

    def init(
        self,
        df,
        source,
        is_stock: bool,
        date_col: Optional[str],
        to_datetime_kwargs: dict,
        time_frame: TimeFrameArg,
        cumulators: Optional[Cumulators]
    ):
        if date_col is not None:
            self._date_col = date_col
            self._to_datetime_kwargs = to_datetime_kwargs

            if is_stock:
                source_cumulator = source._cumulator

                if source_cumulator._date_col is None:
                    # Which means the source stock data frame has no date column, so we have to apply it
                    apply_date_to_df(df, date_col, to_datetime_kwargs)
                elif source_cumulator._date_col != date_col:
                    raise ValueError(f'refuse to set date column as "{date_col}" since the original stock data frame already have a date column "{source_cumulator._date_col}"')
            else:
                apply_date_to_df(df, date_col, to_datetime_kwargs)
        else:
            if is_stock:
                # We should copy the source's cumulator settings
                self._merge_date_col(source._cumulator)
            else:
                self._date_col = None

        if time_frame is None:
            if is_stock:
                self._merge_time_frame(source._cumulator)
            else:
                self._time_frame = None

            return

        self._time_frame = TimeFrame.ensure(time_frame)

        self._cumulators = (
            # None means use the default cumulators
            cumulators if cumulators is not None
            else self.CUMULATORS
        ).copy()

        self._to_cumulate = None
        self._to_cumulate_inited = False

    def _merge_date_col(self, source_cumulator: '_Cumulator'):
        self._date_col = source_cumulator._date_col

        if source_cumulator._date_col is None:
            return

        self._to_datetime_kwargs = source_cumulator._to_datetime_kwargs

    def _merge_time_frame(self, source_cumulator: '_Cumulator'):
        self._time_frame = source_cumulator._time_frame

        if source_cumulator._time_frame is None:
            return

        self._cumulators = source_cumulator._cumulators.copy()
        self._to_cumulate = source_cumulator._to_cumulate
        self._to_cumulate_inited = source_cumulator._to_cumulate_inited

    def add(self, column_name, cumulator: Cumulator):
        self._cumulators[column_name] = cumulator

    def append(
        self,
        to,
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

        return DataFrame.append(to, other, *args, **kwargs)

    def cum_append(
        self,
        to,
        # TODO:
        # support other types
        other: DataFrame,
        *args, **kwargs
    ):
        if self._date_col is None or self._time_frame is None:
            raise ValueError('date_col and time_frame must be specified before calling cum_append()')

        if not len(other):
            raise ValueError('the data frame to be appended is empty')

        other = self._convert_to_date_df(other)

        last_timestamp = (
            None if self._to_cumulate is None
            else self._to_cumulate.iloc[-1].name
        )

        start = None
        last = None
        to_append: ToAppend = []

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
                    None if last is None else other[start:last],
                    to_append
                )

                start = timestamp

            last = timestamp

        self._to_cumulate = other[start:]

        # Append the rows even the latest time frame is not closed
        self._pre_append(self._to_be_cumulated)

        return append(to, to_append, *args, **kwargs)

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

    def _cumulate(
        self,
        to_cumulate: Optional[DataFrame],
        to_append: ToAppend
    ):
        to_cumulate = [
            item
            for item in [to_cumulate, self._to_cumulate]
            if item is not None
        ]
        self._to_cumulate = None

        if not to_cumulate:
            return

        if len(to_cumulate) == 2:
            to_cumulate = concat(to_cumulate)
            self._pre_append(to_cumulate, to_append)
        else:
            self._pre_append(to_cumulate[0], to_append)

    def _pre_append(
        self,
        to_cumulate: DataFrame,
        to_append: ToAppend
    ):
        if len(to_cumulate) == 1:
            # We do not need to cumulate
            to_append.append(to_cumulate)
            return

        # Use the values of the last row except columns of self._cumulators
        cumulated = to_cumulate.iloc[-1].copy()

        # Use the index of the first row
        cumulated.rename(to_cumulate.iloc[0].name)

        for column_name in cumulated.index:
            cumulator = self._cumulators.get(column_name)

            if cumulator is not None:
                cumulated[column_name] = cumulator(
                    cumulated[column_name].to_numpy()
                )

        to_append.append(cumulated)


class CumulatorMixin:
    @property
    def _cumulator(self) -> _Cumulator:
        cumulator = getattr(self, KEY_CUMULATOR, None)

        if cumulator is None:
            cumulator = _Cumulator()
            set_attr(self, KEY_CUMULATOR, cumulator)

        return cumulator
