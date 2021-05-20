from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Tuple
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

from .utils import (
    ColumnInfo,

    init_stock_metas,
    copy_stock_metas,
    copy_clean_stock_metas
)

from .date import (
    apply_date,
    apply_date_to_df
)

from .time_frame import (
    TimeFrame,
    TimeFrameArg,
    ensure_time_frame
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


cumulators: Cumulators = {
    'open': first,
    'high': high,
    'low': low,
    'close': last,
    'volume': add
}


def cum_append_type_error(date_col: Optional[str] = None) -> ValueError:
    message = 'the target to be `cum_append()`ed must have a DatetimeIndex'

    if date_col is None:
        return ValueError(message)

    return ValueError(f'{message} or a "{date_col}" column')


def cum_append(
    df: 'MetaDataFrame',
    other: ToAppend
) -> Tuple[DataFrame, 'MetaDataFrame']:
    """
    Returns:
        Tuple[DataFrame, StockDataFrame]: this method does not ensure that the return type is MetaDataFrame due to the limitation of DataFrame.append
    """

    duplicates = df[other[0].name:]
    other = DataFrame(other)

    if (df.columns.get_indexer(other.columns) >= 0).all():
        other = other.reindex(columns=df.columns)

    length = len(duplicates)
    if length:
        # Do not drop duplicates, because for now
        # StockDataFrame will loose column info if drop rows
        df = df._slice(slice(0, - length))

    return concat([df, other]), df


def ensure_type(
    df: DataFrame,
    source: 'MetaDataFrame'
) -> 'MetaDataFrame':
    if isinstance(df, MetaDataFrame):
        df._cumulator.update(df, source)
        copy_stock_metas(source, df)
    else:
        df = source._constructor(df, source=source)

    return df


class _Cumulator:
    _to_append: ToAppend

    _date_col: Optional[str] = None
    _time_frame: Optional[TimeFrame] = None
    _unclosed: Optional[DataFrame] = None
    _cumulators: Cumulators = cumulators.copy()

    def update(
        self,
        df: 'MetaDataFrame',
        source,
        source_cumulator: '_Cumulator' = None,
        date_col: Optional[str] = None,
        to_datetime_kwargs: dict = {},
        time_frame: TimeFrameArg = None,
        cumulators: Optional[Cumulators] = None
    ):
        # TODO:
        # Split the logic about is_meta_frame

        is_meta_frame = isinstance(source, MetaDataFrame)

        if is_meta_frame and source_cumulator is None:
            source_cumulator = source._cumulator

        if date_col is not None:
            self._date_col = date_col
            self._to_datetime_kwargs = to_datetime_kwargs

            if is_meta_frame:
                if source_cumulator._date_col is None:
                    # Which means the source stock data frame has no date column, so we have to apply it
                    apply_date_to_df(
                        df,
                        date_col,
                        to_datetime_kwargs,
                        check=True
                    )
                elif source_cumulator._date_col != date_col:
                    raise ValueError(f'refuse to set date column as "{date_col}" since the original stock data frame already have a date column "{source_cumulator._date_col}"')
            else:
                apply_date_to_df(
                    df,
                    date_col,
                    to_datetime_kwargs,
                    check=True
                )
        else:
            if is_meta_frame:
                # We should copy the source's cumulator settings
                self._merge_date_col(source_cumulator)
            else:
                self._date_col = None

        if time_frame is None:
            if is_meta_frame:
                self._merge_time_frame(source_cumulator)
                self._merge_unclosed(source_cumulator, df, source)
        else:
            self._time_frame = ensure_time_frame(time_frame)

        if cumulators is None:
            if is_meta_frame:
                self._cumulators = source_cumulator._cumulators
        else:
            # StockDataFrame(stockdataframe, cumulators=cumulators)
            self._cumulators = cumulators

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

    def _merge_unclosed(
        self,
        source_cumulator: '_Cumulator',
        df: 'MetaDataFrame',
        source: 'MetaDataFrame'
    ):
        unclosed = source_cumulator._unclosed

        if unclosed is None or not len(df) or not len(source):
            return

        if df.iloc[-1].name == source.iloc[-1].name:
            self._unclosed = unclosed

    def apply_date_col(self, other):
        if self._date_col is not None:
            other = apply_date(
                self._date_col,
                self._to_datetime_kwargs,
                True,
                other
            )

        return other

    def cum_append(
        self,
        to: 'MetaDataFrame',
        # TODO:
        # support other types
        other: DataFrame
    ) -> Tuple[DataFrame, DataFrame, 'MetaDataFrame']:
        # It is allowed to have a None date_col,
        # but `other` must have a DatetimeIndex
        if self._time_frame is None:
            raise ValueError('refuse to cum_append() a stock data frame without time_frame specified')

        if not len(other):
            raise ValueError('the data frame to be appended is empty')

        current_unclosed = self._unclosed

        other = self._convert_to_date_df(other)

        last_timestamp = (
            None if self._unclosed is None
            else self._unclosed.iloc[-1].name
        )

        start = None
        last = None
        self._to_append = []

        for timestamp in other.index:
            if not isinstance(timestamp, Timestamp):
                raise cum_append_type_error(self._date_col)

            if start is None:
                start = timestamp

            if last_timestamp is None:
                last_timestamp = timestamp
                last = timestamp
                continue

            if (
                self._time_frame.unify(last_timestamp)
                != self._time_frame.unify(timestamp)
            ):
                self._cumulate(
                    # For a data frame of TimestampIndex,
                    # indexing are performed in a close range
                    None if last is None else other[start:last]
                )
                self._pre_append(True)

                start = timestamp
                last_timestamp = timestamp

            last = timestamp

        self._cumulate(other[start:])
        # Append the rows even the latest time frame is not closed
        self._pre_append()

        new, source = cum_append(to, self._to_append)
        self._to_append.clear()

        unclosed = self._unclosed

        # TODO:
        # Do not ruin self._unclosed
        self._unclosed = current_unclosed

        return new, unclosed, source

    def _convert_to_date_df(
        self,
        other: DataFrame
    ) -> DataFrame:
        date_col = self._date_col

        if date_col is not None and date_col in other.columns:
            other = other.copy()
            apply_date_to_df(other, date_col, self._to_datetime_kwargs)

        return other

    def _cumulate(
        self,
        to_cumulate: Optional[DataFrame]
    ) -> None:
        """
        Concat the givin data frame to self._unclosed
        """

        unclosed = self._unclosed

        # Logically, at least one of unclosed and to_cumulate is not None.

        if to_cumulate is None:
            return

        if unclosed is None:
            self._unclosed = to_cumulate
            return

        self._unclosed = concat([unclosed, to_cumulate])

    def _pre_append(
        self,
        clean: bool = False
    ):
        """
        Cumulate self._unclosed and append to self._to_append

        Args:
            clean (:obj:`bool`, optional): True then clean self._unclosed
        """

        unclosed = self._unclosed

        has_duplicates = False
        last = None
        retain = []
        index = unclosed.index

        for timestamp in index:
            if last is None:
                last = timestamp
                continue

            if timestamp == last:
                # Which means there is a record of the same timestamp,
                # we do not cumulate them but update it.
                has_duplicates = True
                retain.append(False)
            else:
                retain.append(True)

            last = timestamp

        retain.append(True)

        if has_duplicates:
            unclosed = unclosed[Series(retain, index=index)]

        if clean:
            self._unclosed = None

        if len(unclosed) == 1:
            # We do not need to cumulate
            self._to_append.append(unclosed.iloc[0])
            return

        # Use the values of the last row except columns of self._cumulators
        cumulated = unclosed.iloc[-1].copy()

        # Use the index of the first row
        cumulated.rename(unclosed.iloc[0].name, inplace=True)

        for column_name in cumulated.index:
            cumulator = self._cumulators.get(column_name)

            if cumulator is not None:
                cumulated[column_name] = cumulator(
                    unclosed[column_name].to_numpy()
                )

        self._to_append.append(cumulated)


class MetaDataFrame(DataFrame):
    """
    The subclass of pandas.DataFrame which ensures return type of all kinds methods to be MetaDataFrame
    """

    _stock_indexer_slice: Optional[slice] = None
    _stock_indexer_axis: int = 0

    _stock_aliases_map: Dict[str, str]
    _stock_columns_info_map: Dict[str, ColumnInfo]

    # Methods that used by pandas and sub classes
    # --------------------------------------------------------------------

    def __finalize__(
        self,
        other,
        method: Optional[str] = None,
        # For now (pandas 1.2.3), args and kwargs are useless,
        # however, let's keep them for forward compatibility
        *args, **kwargs
    ) -> 'MetaDataFrame':
        """
        Propagate metadata from other to self.

        This method overrides `DataFrame.__finalize__`
        which ensures the meta info of StockDataFrame
        """

        super().__finalize__(other, method, *args, **kwargs)

        if method != 'append' and method != 'concat':
            # append:
            # DataFrame.append is implemented with pandas.concat which
            # does not ensure the return type as `self._constructor`.
            # So we will handle method append specially

            # concat:
            # Inside pandas.concat, other is `_Concatenator`
            copy_clean_stock_metas(
                other,
                self,
                other._stock_indexer_slice,
                other._stock_indexer_axis
            )

            self._cumulator.update(self, other)

        return self

    def _slice(self, slice_obj: slice, axis: int = 0) -> 'MetaDataFrame':
        """
        This method is called in several cases, self.iloc[slice] for example

        We mark the slice and axis here to prevent extra calculations
        """

        self._stock_indexer_slice = slice_obj
        self._stock_indexer_axis = axis

        try:
            result = super()._slice(slice_obj, axis)
        except Exception as e:
            raise e
        finally:
            self._stock_indexer_slice = None
            self._stock_indexer_axis = 0

        return result

    # --------------------------------------------------------------------

    def __init__(
        self,
        data=None,
        # from_constructor: Optional[bool] = bool,
        date_col: Optional[str] = None,
        to_datetime_kwargs: dict = {},
        time_frame: TimeFrameArg = None,
        cumulators: Optional[Cumulators] = None,
        source: Optional['MetaDataFrame'] = None,
        *args,
        **kwargs
    ) -> None:
        """
        Creates a stock data frame

        Args:
            data (ndarray, Iterable, dict, DataFrame, StockDataFrame): data
            date_col (:obj:`str`, optional): If set, then the column named `date_col` will convert and set as the DateTimeIndex of the data frame
            to_datetime_kwargs (dict): the keyworded arguments to be passed to `pandas.to_datetime()`. It only takes effect if `date_col` is specified.
            time_frame (str, TimeFrame): defines the time frame of the stock
            source (:obj:`StockDataFrame`, optional): the source to copy meta data from if the source is a StockDataFrame. Defaults to `data`
            cumulators (:obj:`Cumulators`, optional): a dict of `Cumulator`s for each column name. A `Cumulator` is a function that accepts an `np.ndarray` as the only parameter and returns a float.
            *args: other pandas.DataFrame arguments
            **kwargs: other pandas.DataFrame keyworded arguments
        """

        DataFrame.__init__(self, data, *args, **kwargs)

        if self.columns.nlevels > 1:
            # For now, I admit,
            # there are a lot of works to support MultiIndex dataframes
            raise ValueError(
                'stock-pandas does not support dataframes with MultiIndex columns'
            )

        if source is None:
            source = data

        is_meta_frame = isinstance(source, MetaDataFrame)

        if is_meta_frame:
            copy_stock_metas(source, self, data is not None)
        else:
            init_stock_metas(self)

        if (
            not is_meta_frame
            and date_col is None
            and time_frame is None
        ):
            # Cases
            # 1.
            # StockDataFrame(dataframe)
            # 2.
            # created by self._constructor(new_data).__finalize__(self)
            # we will update cumulator data in __finalize__
            return

        # Cases
        # 1.
        # StockDataFrame(stockdataframe)
        # 2.
        # StockDataFrame(dataframe, date_col='time')

        self._cumulator.update(
            self,
            source,
            date_col=date_col,
            to_datetime_kwargs=to_datetime_kwargs,
            time_frame=time_frame,
            cumulators=cumulators
        )

    @property
    def _cumulator(self) -> _Cumulator:
        cumulator = getattr(self, KEY_CUMULATOR, None)

        if cumulator is None:
            cumulator = _Cumulator()
            set_attr(self, KEY_CUMULATOR, cumulator)

        return cumulator

    # Public Methods of stock-pandas
    # --------------------------------------------------------------------

    def cumulate(self) -> 'MetaDataFrame':
        """
        Cumulate the current data frame by its time frame, and returns a new object

        Returns:
            StockDataFrame
        """

        return self._constructor(source=self).cum_append(self)

    def append(self, other, *args, **kwargs) -> 'MetaDataFrame':
        """
        Appends row(s) of other to the end of caller, applying date_col to the newly-appended row(s) if possible, and returning a new object

        The args of this method is the same as `pandas.DataFrame.append`
        """

        other = self._cumulator.apply_date_col(other)
        appended = super().append(other, *args, **kwargs)

        return ensure_type(appended, self)

    def cum_append(
        self,
        other: DataFrame
    ) -> 'MetaDataFrame':
        """
        Appends row(s) of other to the end of caller, applies cumulation to these rows, and returns a new object

        Args:
            other (DataFrame): the new data frame to append
        """

        concatenated, unclosed, source = self._cumulator.cum_append(
            self, other
        )

        df = ensure_type(concatenated, source)
        df._cumulator._unclosed = unclosed

        return df
